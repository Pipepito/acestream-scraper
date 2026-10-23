"""Contributor branches cannot choose host code or reuse a stale approval."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


policy = module("collaboration_policy", "scripts/ops/prepare_jenkins_collaboration.py")
revision = module("pr_revision", "scripts/ci/verify_pr_revision.py")
HEAD = "a" * 40
BASE = "b" * 40
POLICY_SHA = "c" * 40
APPROVER = "test-maintainer"
JOB = "/validation/approved-images"


def pr():
    return {"number": 12, "state": "open", "merged": False,
            "base": {"sha": BASE, "ref": "develop", "repo": {"full_name": revision.REPOSITORY}},
            "head": {"sha": HEAD, "ref": "feature", "repo": {"full_name": "contributor/fork"}}}


@pytest.mark.parametrize("same_repository", [False, True])
def test_forks_and_collaborator_heads_require_the_same_exact_revision(same_repository):
    data = pr()
    if same_repository:
        data["head"]["repo"]["full_name"] = revision.REPOSITORY
    revision.verify(data, "12", HEAD, BASE, "develop")


@pytest.mark.parametrize("section,key,value", [
    ("head", "sha", "c" * 40), ("base", "sha", "c" * 40),
    ("base", "ref", "main"), ("base", "repo", {"full_name": "attacker/repo"}),
    (None, "state", "closed"), (None, "merged", True), (None, "number", 13),
])
def test_approval_is_invalidated_by_head_base_target_or_pr_changes(section, key, value):
    data = pr()
    (data[section] if section else data)[key] = value
    with pytest.raises(ValueError):
        revision.verify(data, "12", HEAD, BASE, "develop")


@pytest.mark.parametrize("field,value", [("pr", "1;id"), ("pr", "0"), ("head", "develop"),
                                         ("base", "b" * 39), ("target", "feature")])
def test_invalid_parameters_fail_before_network(field, value):
    values = dict(pr="12", head=HEAD, base=BASE, target="develop")
    values[field] = value
    with pytest.raises(ValueError):
        revision.validate_identity(**values)


def test_release_pr_cannot_impersonate_develop_from_a_fork():
    data = pr()
    data["base"]["ref"] = "main"
    data["head"]["ref"] = "develop"
    with pytest.raises(ValueError):
        revision.verify(data, "12", HEAD, BASE, "main")
    data["head"]["repo"]["full_name"] = revision.REPOSITORY
    revision.verify(data, "12", HEAD, BASE, "main")


def original_config():
    return f'''<org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject>
      <sources><data><jenkins.branch.BranchSource><source class="{policy.SOURCE}">
      <repoOwner>Pipepito</repoOwner><repository>acestream-scraper</repository>
      <credentialsId>test-status-only</credentialsId><traits>
      <org.jenkinsci.plugins.github_branch_source.BranchDiscoveryTrait><strategyId>3</strategyId></org.jenkinsci.plugins.github_branch_source.BranchDiscoveryTrait>
      <{policy.ORIGIN}><strategyId>1</strategyId></{policy.ORIGIN}>
      <{policy.FORK}><strategyId>1</strategyId><trust class="{policy.FORK}$TrustEveryone"/></{policy.FORK}>
      <org.jenkinsci.plugins.github_branch_source.TagDiscoveryTrait/>
      </traits></source></jenkins.branch.BranchSource></data></sources>
      <factory class="org.jenkinsci.plugins.workflow.multibranch.WorkflowBranchProjectFactory"><scriptPath>jenkins/pr.Jenkinsfile</scriptPath></factory>
      </org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject>'''


def prepared():
    automatic, privileged = policy.render(APPROVER, JOB, POLICY_SHA)
    return policy.configure_pr(original_config()), policy.privileged_xml(privileged), automatic


def test_config_migration_removes_all_branch_supplied_pipeline_paths():
    xml, child, automatic = prepared()
    policy.audit(xml, child, automatic, APPROVER, JOB, POLICY_SHA)
    root = ET.fromstring(xml)
    assert not root.findall(".//scriptPath")
    assert root.findtext(".//credentialsId") == "test-status-only"
    assert policy.configure_pr(xml) == xml
    assert "__PRIVILEGED_JOB__" not in automatic
    assert not ET.fromstring(child).findall(".//credentialsId")
    assert {node.text for node in ET.fromstring(child).findall(".//parameterDefinitions/*/name")} == {
        "PR_NUMBER", "HEAD_SHA", "BASE_SHA", "TARGET_BRANCH"}


@pytest.mark.parametrize("mutation", ["scm_factory", "trusted_forks", "merge_revision", "branch_discovery",
                                       "changed_pipeline", "changed_child", "child_scm", "child_trigger", "child_property_trigger"])
def test_configuration_audit_rejects_trust_regressions(mutation):
    xml, child, automatic = prepared()
    root, child_root = ET.fromstring(xml), ET.fromstring(child)
    if mutation == "scm_factory":
        root.find("factory").set("class", "org.jenkinsci.plugins.workflow.multibranch.WorkflowBranchProjectFactory")
    elif mutation == "trusted_forks":
        root.find(".//" + policy.FORK + "/trust").set("class", policy.FORK + "$TrustPermission")
    elif mutation == "merge_revision":
        root.find(".//" + policy.ORIGIN + "/strategyId").text = "1"
    elif mutation == "branch_discovery":
        ET.SubElement(root.find(".//traits"), "org.jenkinsci.plugins.github_branch_source.BranchDiscoveryTrait")
    elif mutation == "changed_pipeline":
        automatic += "\nload 'jenkins/pr.Jenkinsfile'\n"
    elif mutation == "changed_child":
        child_root.find("definition/script").text += "\nwithCredentials([]) {}\n"
    elif mutation == "child_scm":
        child_root.find("definition").set("class", "org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition")
    elif mutation == "child_trigger":
        ET.SubElement(child_root.find("triggers"), "hudson.triggers.TimerTrigger")
    elif mutation == "child_property_trigger":
        prop = ET.SubElement(child_root.find("properties"), "org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty")
        ET.SubElement(ET.SubElement(prop, "triggers"), "hudson.triggers.TimerTrigger")
    with pytest.raises(ValueError):
        policy.audit(ET.tostring(root, encoding="unicode"), ET.tostring(child_root, encoding="unicode"),
                     automatic, APPROVER, JOB, POLICY_SHA)


@pytest.mark.parametrize("approver,job", [("anyone,authenticated", JOB), ("x'", JOB),
                                         (APPROVER, "relative/job"), (APPROVER, "/../job"),
                                         (APPROVER, "/job'; sh 'oops")])
def test_configuration_inputs_cannot_inject_groovy_or_broaden_approval(approver, job):
    with pytest.raises(ValueError):
        policy.render(approver, job, POLICY_SHA)


def test_automatic_pipeline_never_executes_head_helpers_or_host_image_builds():
    automatic, privileged = policy.render(APPROVER, JOB, POLICY_SHA)
    assert "env.PR_VALIDATION_REF = env.CHANGE_FORK" not in automatic
    assert ": 'HEAD'" not in automatic
    assert "validate_pr_images.sh" not in automatic
    assert "bootstrap_jenkins_runner.sh" not in automatic
    assert "withCredentials" not in automatic + privileged
    assert "load " not in "\n".join(line for line in automatic.splitlines() if not line.startswith("//"))
    assert "wait: true, propagate: true" in automatic
    assert automatic.index("deleteDir()") < automatic.index("stage('Owner-approved validation')")
    assert privileged.index("submitter:") < privileged.index("lock(resource:")
    assert privileged.count("python3 -I trusted/verify_pr_revision.py") == 3
    assert "__PR_APPROVER__" not in privileged
    assert "__POLICY_SHA__" not in privileged
    assert f"TRUSTED_POLICY_SHA = '{POLICY_SHA}'" in privileged


def test_revision_check_fails_closed_on_unavailable_github(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["verify", "--pr", "12", "--head", HEAD, "--base", BASE, "--target", "develop"])
    def unavailable(*args, **kwargs):
        raise OSError("private connection diagnostic")
    monkeypatch.setattr(revision.urllib.request, "urlopen", unavailable)
    assert revision.main() == 1
    assert "private connection" not in capsys.readouterr().out


def test_preparer_creates_private_artifacts_without_overwriting(tmp_path):
    source = tmp_path / "input.xml"
    source.write_text(original_config())
    destination = tmp_path / "prepared"
    command = [sys.executable, str(ROOT / "scripts/ops/prepare_jenkins_collaboration.py"),
               "--pr-config", str(source), "--approver", APPROVER, "--privileged-job", JOB,
               "--policy-sha", POLICY_SHA,
               "--output", str(destination)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout
    assert APPROVER not in result.stdout and JOB not in result.stdout
    assert destination.stat().st_mode & 0o777 == 0o700
    assert (destination / "pr-job.xml").stat().st_mode & 0o777 == 0o600
    assert subprocess.run(command, capture_output=True).returncode == 1


@pytest.mark.parametrize("container_failure", [False, True])
def test_approved_gate_has_no_network_or_credentials_and_blocks_images_on_test_failure(tmp_path, container_failure):
    import os
    source, trusted, binaries = (tmp_path / name for name in ("source", "trusted", "bin"))
    for path in (source, trusted, binaries):
        path.mkdir()
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--allow-empty", "-qm", "Fixture"], check=True)
    head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    log = tmp_path / "calls"
    (trusted / "build_pr_runner.sh").write_text('''#!/bin/bash
printf 'runner\\n' >> "$CALLS"
while [[ $# -gt 0 ]]; do
  if [[ "$1" = --image-file ]]; then printf 'test-runner' > "$2"; break; fi
  shift
done
''')
    (trusted / "bootstrap_jenkins_runner.sh").write_text('printf "bootstrap\\n" >> "$CALLS"\n')
    (trusted / "validate_pr_images.sh").write_text('printf "images:%s\\n" "$PR_IMAGE_SOURCE_ROOT" >> "$CALLS"\n')
    docker = binaries / "docker"
    docker.write_text('''#!/bin/bash
printf '%s\\n' "$*" >> "$CALLS"
if [[ "$1" = run && "$FAIL_CONTAINER" = 1 ]]; then exit 23; fi
''')
    docker.chmod(0o755)
    environment = {**os.environ, "PATH": str(binaries) + os.pathsep + os.environ["PATH"],
                   "BUILD_NUMBER": "42", "HEAD_SHA": head, "BASE_SHA": BASE,
                   "CALLS": str(log), "FAIL_CONTAINER": "1" if container_failure else "0"}
    result = subprocess.run(["bash", str(ROOT / "scripts/ci/run_approved_pr_validation.sh"), str(source), str(trusted)],
                            env=environment, capture_output=True, text=True)
    calls = log.read_text()
    assert result.returncode == (23 if container_failure else 0), result.stderr
    assert "--network none --read-only" in calls
    assert "--cap-drop ALL --security-opt no-new-privileges" in calls
    assert "docker.sock" not in calls and "withCredentials" not in calls
    assert "rm --force acestream-approved-pr-42" in calls
    assert ("images:" in calls) is not container_failure
    assert ("bootstrap" in calls) is not container_failure
    if not container_failure:
        assert f"images:{source}" in calls
    log.unlink()
    environment["HEAD_SHA"] = HEAD
    result = subprocess.run(["bash", str(ROOT / "scripts/ci/run_approved_pr_validation.sh"), str(source), str(trusted)],
                            env=environment, capture_output=True, text=True)
    assert result.returncode != 0
    assert not log.exists(), "A mismatched checkout must fail before any runner/image work"


def test_embedded_pipeline_shell_scripts_parse(tmp_path):
    import re
    for name in ("pr.Jenkinsfile", "pr-privileged.Jenkinsfile"):
        text = (ROOT / "jenkins" / name).read_text()
        for index, script in enumerate(re.findall(r"'''(.*?)'''", text, re.DOTALL)):
            path = tmp_path / f"{name}-{index}.sh"
            path.write_text(script)
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("policy_ref", ["develop", "HEAD", "refs/pull/12/head", "c" * 39, "c" * 40 + ";id"])
def test_privileged_policy_cannot_follow_a_moving_or_injected_ref(policy_ref):
    with pytest.raises(ValueError):
        policy.render(APPROVER, JOB, policy_ref)
