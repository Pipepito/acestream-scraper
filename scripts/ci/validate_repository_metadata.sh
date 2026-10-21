#!/usr/bin/env bash
# Invoke only a trusted copy of this script and its sibling metadata-tools/.
set -euo pipefail
validator_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="${1:?Usage: validate_repository_metadata.sh REPOSITORY_ROOT}"
tool_dir="$(mktemp -d "${TMPDIR:-/tmp}/repository-metadata.XXXXXX")"
trap 'rm -rf "$tool_dir"' EXIT
for file in package.json package-lock.json validate.cjs test.cjs assignment-workflow.json; do
  cp "$validator_dir/metadata-tools/$file" "$tool_dir/$file"
done
# The target-owned lockfile selects two parser packages. No application dependency
# installation, lifecycle scripts, repository npm config, or Docker is involved.
(
  cd "$tool_dir"
  npm ci --ignore-scripts --no-audit --no-fund --prefer-offline
  node --test test.cjs
  node validate.cjs "$root"
)
