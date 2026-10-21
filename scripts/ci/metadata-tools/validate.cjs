'use strict';

// This script and its dependencies must come from the trusted validation ref.
// Repository YAML/JSON is input data, never code or dependency configuration.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const yaml = require('js-yaml');

function check(condition, message) {
  if (!condition) throw new Error(message);
}

function bounded(value, seen = new Set(), depth = 0) {
  check(depth <= 30, 'metadata nesting exceeds 30 levels');
  if (value && typeof value === 'object') {
    check(!seen.has(value), 'YAML aliases and cycles are not supported');
    seen.add(value);
    for (const child of Object.values(value)) bounded(child, seen, depth + 1);
  }
  return value;
}

function parse(text) {
  check(Buffer.byteLength(text) <= 256 * 1024, 'metadata exceeds 256 KiB');
  return bounded(yaml.load(text, {schema: yaml.JSON_SCHEMA}));
}

function form(value, config = false) {
  check(value && typeof value === 'object' && !Array.isArray(value), 'expected a mapping');
  if (config) {
    if ('blank_issues_enabled' in value) check(typeof value.blank_issues_enabled === 'boolean', 'blank_issues_enabled must be boolean');
    if ('contact_links' in value) {
      check(Array.isArray(value.contact_links), 'contact_links must be a list');
      for (const link of value.contact_links) {
        check(typeof link.name === 'string' && typeof link.about === 'string', 'contact link needs name and about');
        check(typeof link.url === 'string' && /^https:\/\//.test(link.url), 'contact link needs an HTTPS URL');
      }
    }
    return;
  }
  check(typeof value.name === 'string' && value.name.trim(), 'form needs a name');
  check(typeof value.description === 'string' && value.description.trim(), 'form needs a description');
  check(Array.isArray(value.body) && value.body.length, 'form needs body fields');
  const ids = new Set();
  const labels = new Set();
  for (const item of value.body) {
    check(item && ['markdown', 'input', 'textarea', 'dropdown', 'checkboxes'].includes(item.type), 'unsupported form field');
    const attrs = item.attributes;
    check(attrs && typeof attrs === 'object', 'field needs attributes');
    if (item.type === 'markdown') {
      check(typeof attrs.value === 'string', 'markdown needs text');
      continue;
    }
    check(typeof item.id === 'string' && /^[a-zA-Z0-9_-]+$/.test(item.id) && !ids.has(item.id), 'invalid or duplicate field ID');
    ids.add(item.id);
    check(typeof attrs.label === 'string' && attrs.label.trim() && !labels.has(attrs.label), 'missing or duplicate field label');
    labels.add(attrs.label);
    if (item.validations && 'required' in item.validations) check(typeof item.validations.required === 'boolean', 'required must be boolean');
    if (['dropdown', 'checkboxes'].includes(item.type)) {
      check(Array.isArray(attrs.options) && attrs.options.length, 'field needs options');
      for (const option of attrs.options) {
        if (item.type === 'dropdown') check(typeof option === 'string', 'dropdown options must be strings');
        else {
          check(option && typeof option.label === 'string', 'checkbox needs a label');
          if ('required' in option) check(typeof option.required === 'boolean', 'checkbox required must be boolean');
        }
      }
    }
  }
}

function ruleset(value) {
  check(value && typeof value.name === 'string' && value.name.trim(), 'ruleset needs a name');
  check(['branch', 'tag'].includes(value.target), 'unsupported ruleset target');
  check(['active', 'disabled', 'evaluate'].includes(value.enforcement), 'invalid enforcement');
  check(Array.isArray(value.rules) && value.rules.every(rule => rule && typeof rule.type === 'string'), 'rules must contain rule objects');
  const ref = value.conditions?.ref_name;
  check(ref && Array.isArray(ref.include) && ref.include.length && Array.isArray(ref.exclude), 'ruleset needs ref conditions');
  check([...ref.include, ...ref.exclude].every(name => typeof name === 'string'), 'ref patterns must be strings');
  check(Array.isArray(value.bypass_actors), 'bypass_actors must be a list');
  for (const actor of value.bypass_actors) {
    check(['User', 'RepositoryRole', 'Team', 'Integration', 'DeployKey', 'OrganizationAdmin'].includes(actor.actor_type), 'invalid bypass actor');
    check(['always', 'pull_request', 'exempt'].includes(actor.bypass_mode), 'invalid bypass mode');
  }
}

function workflow(value, expected) {
  // Exact parsed equality permits comments/formatting, but changes to executable
  // behavior or permissions must update this trusted policy through the full gate.
  assert.deepStrictEqual(value, expected, 'assignment workflow differs from trusted metadata-only policy');
}

function read(root, relative) {
  let current = root;
  for (const part of relative.split('/')) {
    current = path.join(current, part);
    check(!fs.lstatSync(current).isSymbolicLink(), 'metadata path contains a symlink');
  }
  const stat = fs.statSync(current);
  check(stat.isFile() && !(stat.mode & 0o111), 'metadata must be a non-executable regular file');
  check(stat.size <= 256 * 1024, 'metadata exceeds 256 KiB');
  return fs.readFileSync(current, 'utf8');
}

function validate(root) {
  let count = 0;
  for (const [directory, suffix, validateValue] of [
    ['.github/ISSUE_TEMPLATE', /\.ya?ml$/, (v, n) => form(v, /^config\.ya?ml$/.test(n))],
    ['.github/rulesets', /\.json$/, ruleset],
  ]) {
    const folder = path.join(root, directory);
    if (!fs.existsSync(folder)) continue;
    check(!fs.lstatSync(path.join(root, '.github')).isSymbolicLink() && !fs.lstatSync(folder).isSymbolicLink(), 'metadata directory contains a symlink');
    const names = fs.readdirSync(folder).filter(name => suffix.test(name));
    check(names.length <= 100, 'too many metadata files');
    for (const name of names) {
      const relative = `${directory}/${name}`;
      const text = read(root, relative);
      const value = directory.endsWith('rulesets') ? bounded(JSON.parse(text)) : parse(text);
      try { validateValue(value, name); } catch (error) { throw new Error(`${relative}: ${error.message}`); }
      count++;
    }
  }
  const assignment = '.github/workflows/assign-pull-requests.yml';
  if (fs.existsSync(path.join(root, assignment))) {
    const expected = JSON.parse(fs.readFileSync(path.join(__dirname, 'assignment-workflow.json'), 'utf8'));
    workflow(parse(read(root, assignment)), expected);
    count++;
  }
  console.log(`PASS: ${count} repository metadata files; no repository code executed`);
}

module.exports = {parse, form, ruleset, workflow, validate};
if (require.main === module) {
  try { validate(path.resolve(process.argv[2] || '.')); }
  catch (error) { console.error(`FAIL: ${error.message}`); process.exitCode = 1; }
}
