"""Public changelog assets must match their Markdown sources."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]

def test_generated_changelog_is_current_and_parser_rejects_unsupported_markup():
    result = subprocess.run(['node', 'frontend/scripts/generate-changelog.js', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    script = """
const assert = require('node:assert/strict');
const {parseNotes} = require('./frontend/scripts/generate-changelog.js');
const text = '# v2.2.0\\nSummary.\\n## Added\\n- Works offline.\\n';
assert.equal(parseNotes(text, 'v2.2.0').sections[0].items[0], 'Works offline.');
assert.ok(parseNotes(text.replace('Works offline.', '[PR #270](https://github.com/Pipepito/acestream-scraper/pull/270)'), 'v2.2.0'));
for (const invalid of [text.replace('Works offline.', '[bad](javascript:alert(1))'), text.replace('Works offline.', '[bad](https://github.com.evil.test/name)'), text.replace('v2.2.0','v2.1.0'), text.replace('- Works offline.', '```html'), text.replace('Works offline.', '<script>'), text.replace('- Works offline.', '')]) {
  assert.throws(() => parseNotes(invalid, 'v2.2.0'));
}
"""
    subprocess.run(['node', '-e', script], cwd=ROOT, check=True)


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

