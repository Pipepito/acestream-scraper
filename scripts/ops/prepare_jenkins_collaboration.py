#!/usr/bin/env python3
"""Prepare/audit administrator-owned Jenkins definitions; never contact Jenkins.

Input/output XML can contain private configuration. Do not commit it. This tool
prints no XML, credential IDs, approver identity, endpoints, or job coordinates.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
FACTORY = "org.jenkinsci.plugins.pipeline.multibranch.defaults.PipelineBranchDefaultsProjectFactory"
SOURCE = "org.jenkinsci.plugins.github_branch_source.GitHubSCMSource"
# XStream XML escapes underscores in element names (not class attributes).
ORIGIN = "org.jenkinsci.plugins.github__branch__source.OriginPullRequestDiscoveryTrait"
FORK = "org.jenkinsci.plugins.github__branch__source.ForkPullRequestDiscoveryTrait"
TRUST = "org.jenkinsci.plugins.github_branch_source.ForkPullRequestDiscoveryTrait$TrustNobody"
SCRIPT_ID = "acestream-isolated-pr-v1"


def source_node(root: ET.Element) -> ET.Element:
    sources = root.findall(f".//source[@class='{SOURCE}']")
    if len(sources) != 1 or len(root.findall(".//sources/data/jenkins.branch.BranchSource/source")) != 1:
        raise ValueError("Expected exactly one GitHub branch source")
    node = sources[0]
    if node.findtext("apiUri") not in (None, "", "https://api.github.com"):
        raise ValueError("Only the public GitHub API is supported")
    if node.findtext("repoOwner") != "Pipepito" or node.findtext("repository") != "acestream-scraper":
        raise ValueError("Unexpected source repository")
    return node


def configure_pr(xml: str) -> str:
    root = ET.fromstring(xml)
    if root.tag != "org.jenkinsci.plugins.workflow.multibranch.WorkflowMultiBranchProject":
        raise ValueError("Expected a multibranch PR job")
    node = source_node(root)
    traits = node.find("traits")
    if traits is None:
        traits = ET.SubElement(node, "traits")
    # Head-only builds bind approval/status to the real contributor commit.
    # No origin, tag, or fork may choose its Jenkinsfile.
    for trait in list(traits):
        if "DiscoveryTrait" in trait.tag:
            traits.remove(trait)
    for tag in (ORIGIN, FORK):
        trait = ET.SubElement(traits, tag)
        ET.SubElement(trait, "strategyId").text = "2"
        if tag == FORK:
            ET.SubElement(trait, "trust", {"class": TRUST})
    old = root.find("factory")
    owner = old.find("owner") if old is not None else None
    if old is not None:
        root.remove(old)
    factory = ET.SubElement(root, "factory", {"class": FACTORY, "plugin": "pipeline-multibranch-defaults"})
    if owner is not None:
        factory.append(copy.deepcopy(owner))
    ET.SubElement(factory, "scriptId").text = SCRIPT_ID
    ET.SubElement(factory, "useSandbox").text = "true"
    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def privileged_xml(script: str) -> str:
    root = ET.Element("flow-definition", {"plugin": "workflow-job"})
    ET.SubElement(root, "description").text = "Owner-approved PR validation; no publication credentials or automatic triggers."
    ET.SubElement(root, "keepDependencies").text = "false"
    properties = ET.SubElement(root, "properties")
    parameter_property = ET.SubElement(properties, "hudson.model.ParametersDefinitionProperty")
    definitions = ET.SubElement(parameter_property, "parameterDefinitions")
    for name in ("PR_NUMBER", "HEAD_SHA", "BASE_SHA", "TARGET_BRANCH"):
        definition = ET.SubElement(definitions, "hudson.model.StringParameterDefinition")
        ET.SubElement(definition, "name").text = name
        ET.SubElement(definition, "defaultValue").text = "develop" if name == "TARGET_BRANCH" else ""
        ET.SubElement(definition, "trim").text = "true"
    definition = ET.SubElement(root, "definition", {
        "class": "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition", "plugin": "workflow-cps"})
    ET.SubElement(definition, "script").text = script
    ET.SubElement(definition, "sandbox").text = "true"
    ET.SubElement(root, "triggers")
    ET.SubElement(root, "disabled").text = "false"
    ET.indent(root)
    return ET.tostring(root, encoding="unicode")


def render(approver: str, job: str, policy_sha: str) -> tuple[str, str]:
    # These are inserted into single-quoted Groovy, never shell-interpolated.
    if not re.fullmatch(r"[0-9a-f]{40}", policy_sha):
        raise ValueError("Host policy must be pinned to a reviewed full commit SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.@-]+", approver):
        raise ValueError("Approver must be one exact Jenkins user ID")
    if not re.fullmatch(r"/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", job):
        raise ValueError("Privileged job must be an absolute Jenkins item path")
    if ".." in job.split("/"):
        raise ValueError("Relative job path components are forbidden")
    automatic = (ROOT / "jenkins/pr.Jenkinsfile").read_text().replace("__PRIVILEGED_JOB__", job).replace("__POLICY_SHA__", policy_sha)
    privileged = (ROOT / "jenkins/pr-privileged.Jenkinsfile").read_text().replace("__PR_APPROVER__", approver).replace("__POLICY_SHA__", policy_sha)
    return automatic, privileged


def audit(pr_xml: str, child_xml: str, managed_script: str, approver: str, job: str, policy_sha: str) -> None:
    root = ET.fromstring(pr_xml)
    node = source_node(root)
    factory = root.find("factory")
    if (factory is None or factory.get("class") != FACTORY or
            factory.findtext("scriptId") != SCRIPT_ID or factory.findtext("useSandbox") != "true"):
        raise ValueError("PR job can select an untrusted pipeline definition")
    traits = node.find("traits")
    if traits is None:
        raise ValueError("Missing PR discovery policy")
    discovered = [x for x in traits if "DiscoveryTrait" in x.tag]
    if len(discovered) != 2 or {x.tag for x in discovered} != {ORIGIN, FORK}:
        raise ValueError("Only origin/fork pull requests may be discovered")
    for tag in (ORIGIN, FORK):
        if traits.findtext(tag + "/strategyId") != "2":
            raise ValueError("PR discovery must build head revisions only")
    trust = traits.find(FORK + "/trust")
    if trust is None or trust.get("class") != TRUST:
        raise ValueError("Fork Jenkinsfiles must never be trusted")
    automatic, privileged = render(approver, job, policy_sha)
    if managed_script != automatic:
        raise ValueError("Managed PR script differs from the reviewed pipeline")
    child = ET.fromstring(child_xml)
    definition = child.find("definition")
    if (definition is None or definition.get("class") != "org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition"
            or definition.findtext("sandbox") != "true" or definition.findtext("script") != privileged):
        raise ValueError("Privileged job must use the reviewed fixed inline pipeline")
    if any(len(triggers) for triggers in child.findall(".//triggers")):
        raise ValueError("Privileged job must not have automatic triggers")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-config", type=Path, required=True)
    parser.add_argument("--approver", required=True)
    parser.add_argument("--policy-sha", required=True)
    parser.add_argument("--privileged-job", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--privileged-config", type=Path)
    parser.add_argument("--managed-script", type=Path)
    args = parser.parse_args()
    try:
        if args.audit:
            if not args.privileged_config or not args.managed_script:
                raise ValueError("Audit requires privileged XML and exported managed script")
            audit(args.pr_config.read_text(), args.privileged_config.read_text(), args.managed_script.read_text(),
                  args.approver, args.privileged_job, args.policy_sha)
            print("PASS: job definitions match reviewed trust policy. Credential scopes and ACLs require separate live inspection.")
        else:
            if args.output is None:
                raise ValueError("A new private output directory is required")
            automatic, privileged = render(args.approver, args.privileged_job, args.policy_sha)
            pr = configure_pr(args.pr_config.read_text())
            child = privileged_xml(privileged)
            audit(pr, child, automatic, args.approver, args.privileged_job, args.policy_sha)
            args.output.mkdir(mode=0o700, parents=False, exist_ok=False)
            files = {"pr-job.xml": pr, "pr-pipeline.groovy": automatic, "privileged-job.xml": child}
            manifest = {}
            for name, content in files.items():
                with (args.output / name).open("x", encoding="utf-8") as stream:
                    os.chmod(stream.name, 0o600)
                    stream.write(content)
                manifest[name] = hashlib.sha256(content.encode()).hexdigest()
            (args.output / "sha256.json").write_text(json.dumps(manifest, indent=2) + "\n")
            print("Prepared private configuration bundle; no Jenkins or GitHub settings changed.")
    except (ValueError, OSError, ET.ParseError) as exc:
        # Avoid printing exception paths/config fragments from private inputs.
        print(f"FAIL: could not prepare/audit configuration ({type(exc).__name__}).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
