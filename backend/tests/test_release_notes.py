"""Release notes provenance and retry safety without Docker/GitHub writes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/ci' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


notes = load('release_notes')
publisher = load('publish_github_release')
SHA = 'a' * 40
BODY = b'# v2.2.0\n\nSummary.\n\n## Added\n\n- Works offline.\n'
DIGEST = 'sha256:' + 'b' * 64


@pytest.fixture
def metadata(monkeypatch):
    monkeypatch.setattr(publisher, 'notes_for', lambda v, s: (BODY, hashlib.sha256(BODY).hexdigest()))
    monkeypatch.setattr(publisher, 'inspect_digest', lambda ref: DIGEST)
    return {'mode': 'promote-latest', 'version': 'v2.2.0', 'git_sha': SHA,
            'source': 'pipepito/acestream-scraper:v2.2.0', 'tags': ['pipepito/acestream-scraper:latest'],
            'source_digest': DIGEST, 'notes_sha256': hashlib.sha256(BODY).hexdigest()}


class FakeGitHub:
    def __init__(self, tag=None, existing=None, fail_release=False):
        self.tag, self.existing, self.fail_release = tag, existing, fail_release
        self.writes = []

    def request(self, method, path, data=None):
        if method == 'GET':
            return self.tag if path.startswith('/git/') else self.existing
        self.writes.append((path, data))
        if path == '/git/refs':
            self.tag = {'object': {'type': 'commit', 'sha': data['sha']}}
        elif path == '/releases':
            if self.fail_release:
                raise ValueError('unavailable')
            self.existing = data
        return data


def test_publish_same_markdown_and_idempotent_retry(metadata):
    api = FakeGitHub()
    publisher.publish(metadata, api)
    assert api.existing['body'].encode() == BODY
    assert api.tag['object']['sha'] == SHA
    assert len(api.writes) == 2
    publisher.publish(metadata, api)
    assert len(api.writes) == 2


def test_partial_failure_retries_without_recreating_tag(metadata):
    api = FakeGitHub(fail_release=True)
    with pytest.raises(ValueError, match='unavailable'):
        publisher.publish(metadata, api)
    api.fail_release = False
    publisher.publish(metadata, api)
    assert [path for path, _ in api.writes].count('/git/refs') == 1
    assert api.existing['body'].encode() == BODY


@pytest.mark.parametrize('field,value', [('mode', 'preflight'), ('dry_run', True),
    ('notes_sha256', 'wrong'), ('source_digest', 'wrong'), ('source', 'other:v2.2.0')])
def test_invalid_evidence_never_writes(metadata, field, value):
    metadata[field] = value
    api = FakeGitHub()
    with pytest.raises(ValueError):
        publisher.publish(metadata, api)
    assert not api.writes


def test_mismatched_tag_or_existing_release_never_overwritten(metadata):
    api = FakeGitHub(tag={'object': {'type': 'commit', 'sha': 'c' * 40}})
    with pytest.raises(ValueError, match='different commit'):
        publisher.publish(metadata, api)
    assert not api.writes
    api.tag['object']['sha'] = SHA
    api.existing = {'body': 'edited', 'draft': False, 'prerelease': False}
    with pytest.raises(ValueError, match='differs'):
        publisher.publish(metadata, api)
    assert not api.writes


def test_annotated_tag_is_peeled():
    responses = iter([{'object': {'type': 'tag', 'sha': 'b' * 40}},
                      {'object': {'type': 'commit', 'sha': SHA}}])
    class API:
        def request(self, *args):
            return next(responses)
    assert publisher.verify_tag(API(), 'v2.2.0', SHA)


def test_notes_are_read_from_built_commit_not_newer_checkout(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    def git(*args):
        return subprocess.check_output(['git', *args], text=True).strip()
    git('init', '-q')
    git('config', 'user.name', 'Test')
    git('config', 'user.email', 'test@example.invalid')
    (tmp_path / 'frontend/changelog').mkdir(parents=True)
    source = tmp_path / 'frontend/changelog/v2.2.0.md'
    source.write_bytes(BODY)
    (tmp_path / 'version.txt').write_text('v2.2.0\n')
    git('add', '.')
    git('commit', '-qm', 'Release')
    sha = git('rev-parse', 'HEAD')
    source.write_text('newer unrelated notes')
    assert notes.notes_for('v2.2.0', sha)[0] == BODY
    with pytest.raises(ValueError, match='different version'):
        notes.notes_for('v2.3.0', sha)


def test_promotion_validates_provenance_before_mutation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    notes.METADATA.write_text('stale success')
    monkeypatch.setattr(notes, 'inspect_digest', lambda ref: DIGEST)
    monkeypatch.setattr(notes, 'run', lambda *args: json.dumps({'annotations': {notes.VERSION: 'v2.2.0', notes.REVISION: SHA, notes.NOTES_HASH: 'wrong'}}))
    monkeypatch.setattr(notes, 'save_notes', lambda *args: 'expected')
    calls = []
    monkeypatch.setattr(notes.subprocess, 'run', lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match='notes differ'):
        notes.promote('v2.2.0', 'repo', 'flavor')
    assert not calls
    assert not notes.METADATA.exists()


def test_generated_changelog_is_current_and_parser_rejects_unsupported_markup():
    result = subprocess.run(['node', 'frontend/scripts/generate-changelog.js', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    script = """
const assert = require('node:assert/strict');
const {parseNotes} = require('./frontend/scripts/generate-changelog.js');
const text = '# v2.2.0\\nSummary.\\n## Added\\n- Works offline.\\n';
assert.equal(parseNotes(text, 'v2.2.0').sections[0].items[0], 'Works offline.');
for (const invalid of [text.replace('v2.2.0','v2.1.0'), text.replace('- Works offline.', '```html'), text.replace('Works offline.', '<script>'), text.replace('- Works offline.', '')]) {
  assert.throws(() => parseNotes(invalid, 'v2.2.0'));
}
"""
    subprocess.run(['node', '-e', script], cwd=ROOT, check=True)


def test_promotion_uses_digest_and_records_built_sha(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(notes, 'inspect_digest', lambda ref: DIGEST)
    monkeypatch.setattr(notes, 'run', lambda *args: json.dumps({'annotations': {
        notes.VERSION: 'v2.2.0', notes.REVISION: SHA, notes.NOTES_HASH: 'expected'}}))
    monkeypatch.setattr(notes, 'save_notes', lambda *args: 'expected')
    calls = []
    monkeypatch.setattr(notes.subprocess, 'run', lambda args, **kwargs: calls.append(args))
    notes.promote('v2.2.0', 'repo', 'flavor')
    create = next(call for call in calls if call[:3] == ['docker', 'buildx', 'imagetools'])
    assert create[-1] == 'repo@' + DIGEST
    metadata = json.loads(notes.METADATA.read_text())
    assert metadata['git_sha'] == SHA
    assert metadata['source_digest'] == DIGEST
    assert metadata['mode'] == 'promote-latest'


def test_github_stage_only_follows_successful_non_dry_promotion():
    pipeline = (ROOT / 'jenkins/release.Jenkinsfile').read_text()
    stage = pipeline.split("stage('Publish GitHub release')")[1].split("stage('Publish release wiki')")[0]
    assert 'when { expression { !params.DRY_RUN && params.PUBLISH_LATEST } }' in stage
    assert "credentialsId: 'github-publish'" in stage
    assert "python3 scripts/ci/publish_github_release.py" in stage
    assert "post {" not in stage  # Never publish from an always/failure handler.


def test_build_rejects_changed_markdown_or_version(tmp_path):
    import shutil
    frontend = tmp_path / 'frontend'
    (frontend / 'scripts').mkdir(parents=True)
    (frontend / 'src/data').mkdir(parents=True)
    shutil.copy(ROOT / 'frontend/scripts/generate-changelog.js', frontend / 'scripts')
    shutil.copytree(ROOT / 'frontend/changelog', frontend / 'changelog')
    shutil.copy(ROOT / 'frontend/src/data/changelog.ts', frontend / 'src/data')
    shutil.copy(ROOT / 'version.txt', tmp_path)
    command = ['node', str(frontend / 'scripts/generate-changelog.js'), '--check']
    assert subprocess.run(command, capture_output=True).returncode == 0
    source = frontend / 'changelog/v2.2.0.md'
    original = source.read_text()
    source.write_text(original + '\n- Test-only release note.\n')
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'Changelog drift' in result.stderr
    source.write_text(original)
    (tmp_path / 'version.txt').write_text('v2.3.0\n')
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and 'must match version.txt' in result.stderr
