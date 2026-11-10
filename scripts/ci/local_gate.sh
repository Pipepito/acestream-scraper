#!/usr/bin/env bash
# Run the local validation tier that matches the current change.
#
# The tier comes from scripts/ci/classify_changes.py, the selector Jenkins uses,
# applied to everything that differs from the target branch (committed, staged,
# unstaged and untracked). See "Completion validation" in AGENTS.md.
#
#   docs         documentation and repository metadata validators
#   application  + contracts, the complete backend/frontend suite, plan dry run
#   images       + manifest validator, every flavour for this machine's native
#                  platform, Docker packaging tests
#
# Other architectures are built by Jenkins. This helper never emulates them.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BASE=""
PLAN=0
FORCED=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base) BASE="${2:?--base needs a ref}"; shift 2 ;;
    --plan) PLAN=1; shift ;;
    --tier) FORCED="${2:?--tier needs docs, application or images}"; shift 2 ;;
    -h|--help)
      echo "Usage: local_gate.sh [--base <ref>] [--plan] [--tier docs|application|images]"
      echo "  --base  target to compare with (default: origin/develop, then develop)"
      echo "  --plan  print the tier and its commands without running them"
      echo "  --tier  raise the tier; a lower tier than the change needs is refused"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$BASE" ]]; then
  for candidate in origin/develop develop; do
    if git rev-parse --verify --quiet "${candidate}^{commit}" >/dev/null; then BASE="$candidate"; break; fi
  done
fi
if [[ -z "$BASE" ]] || ! merge_base="$(git merge-base "$BASE" HEAD 2>/dev/null)"; then
  echo "Cannot find a common ancestor with the target branch; pass --base <ref>." >&2
  exit 2
fi

changed="$(mktemp "${TMPDIR:-/tmp}/local-gate.XXXXXX")"
trap 'rm -f "$changed"' EXIT
{
  git diff --no-ext-diff --no-renames --name-only -z "$merge_base"
  git ls-files --others --exclude-standard -z
} > "$changed"

# Prints: <tier> <metadata> <browser> <live>
selection="$(python3 - "$changed" <<'PY'
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('selection', 'scripts/ci/classify_changes.py')
selection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selection)
paths = sorted(set(filter(None, Path(sys.argv[1]).read_bytes().decode().split('\0'))))
if not paths:
    print('none false false false')
    raise SystemExit
result = selection.classify_paths(paths)
tier = 'images' if result['IMAGES'] else 'application' if result['APPLICATION'] else 'docs'
application = [p for p in paths if selection.classify_paths([p])['APPLICATION']]
browser = any(p.startswith(('frontend/', 'e2e/')) for p in application)
# Behaviour that only the live stack exercises: playback, engines, tuner,
# recordings and the journeys themselves. Image-tier changes always qualify.
LIVE = ('backend/app/services/player', 'backend/app/services/tuner', 'backend/app/services/stream',
        'backend/app/services/playback', 'backend/app/services/recording', 'backend/app/services/engine_client',
        'backend/app/services/hls_', 'backend/app/services/cast', 'backend/app/services/remote_players/',
        'backend/app/services/media_servers/', 'backend/app/api/endpoints/player', 'backend/app/api/endpoints/tuner',
        'backend/app/api/endpoints/recordings', 'backend/app/api/endpoints/streams', 'backend/app/api/endpoints/cast',
        'e2e/tests/', 'e2e/src/', 'e2e/stack/', 'e2e/scenarios/', 'e2e/playwright')
live = tier == 'images' or any(p.startswith(LIVE) for p in application)
print(tier, str(result['METADATA']).lower(), str(browser).lower(), str(live).lower())
PY
)"
read -r tier metadata browser live <<< "$selection"

if [[ "$tier" == none ]]; then
  echo "No changes relative to $BASE; nothing to validate."
  exit 0
fi
rank() { case "$1" in docs) echo 1 ;; application) echo 2 ;; images) echo 3 ;; *) echo 0 ;; esac; }
if [[ -n "$FORCED" ]]; then
  if [[ "$(rank "$FORCED")" -eq 0 ]]; then echo "--tier must be docs, application or images." >&2; exit 2; fi
  if [[ "$(rank "$FORCED")" -lt "$(rank "$tier")" ]]; then
    echo "This change needs the $tier tier; refusing to lower it to $FORCED." >&2
    exit 2
  fi
  tier="$FORCED"
fi

steps=(
  "documentation|python3 scripts/ci/validate_documentation.py"
  "docker docs contract|python3 scripts/ci/validate_docker_docs_contract.py"
  "command builder|bash scripts/ci/validate_command_builder.sh"
)
if [[ "$metadata" == true ]]; then
  steps+=("repository metadata|bash scripts/ci/validate_repository_metadata.sh \"\$PWD\"")
fi
if [[ "$(rank "$tier")" -ge 2 ]]; then
  steps+=(
    "legacy paths|bash scripts/ci/assert_no_legacy_paths.sh --strict"
    "runtime script syntax|bash -n entrypoint.sh warp-setup.sh healthcheck.sh"
    "dockerfile contract|backend/venv/bin/python scripts/ci/validate_dockerfile_contract.py"
    "runtime contract|bash scripts/ci/validate_runtime_contract.sh"
    "backend and frontend suite|bash scripts/ci/run_v2_test_suite.sh --profile full"
    "architecture plan dry run|backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py --profile quick"
  )
  if [[ "$browser" == true ]]; then
    steps+=("mocked browser suite|(cd e2e && npm run test:mobile)")
  fi
fi
if [[ "$tier" == images ]]; then
  native="linux/$(docker version --format '{{.Server.Arch}}' 2>/dev/null || true)"
  steps+=(
    "docker manifests|python3 scripts/ci/validate_docker_manifest_metadata.py"
    "native flavour builds|PLATFORM=$native bash scripts/ci/validate_docker_flavor_targets.sh"
    "docker packaging tests|PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker"
  )
fi

echo "Change relative to $BASE needs the '$tier' tier ($(tr '\0' '\n' < "$changed" | grep -c . || true) paths)."
for step in "${steps[@]}"; do printf '  %-28s %s\n' "${step%%|*}" "${step#*|}"; done
if [[ "$live" == true ]]; then
  echo "  live journey                 not run by this helper; follow the safe run sequence in e2e/AGENTS.md"
fi
echo "Cross-architecture image builds are left to Jenkins."
if [[ "$PLAN" -eq 1 ]]; then exit 0; fi

# Prerequisites for this tier are outstanding validation when missing, not passes.
blocked=()
if [[ "$(rank "$tier")" -ge 2 ]]; then
  [[ -x backend/venv/bin/pytest ]] || blocked+=("backend/venv is missing; see Common Commands in AGENTS.md")
  [[ -d frontend/node_modules ]] || blocked+=("frontend/node_modules is missing; run 'cd frontend && npm ci'")
  if [[ -z "${FFMPEG_TEST_TOOL_PATH:-}" ]] && ! command -v ffmpeg >/dev/null 2>&1; then
    blocked+=("FFmpeg is missing; the media tests need it on PATH (or FFMPEG_TEST_TOOL_PATH)")
  fi
fi
if [[ "$tier" == images ]] && ! docker info >/dev/null 2>&1; then
  blocked+=("Docker is not reachable; start it (or grant access to its socket) for the image tier")
fi
if [[ "${#blocked[@]}" -gt 0 ]]; then
  echo "Blocked before running anything:" >&2
  for reason in "${blocked[@]}"; do echo "  - $reason" >&2; done
  exit 3
fi

logs=".quality-reports/local-gate"
rm -rf "$logs"
mkdir -p "$logs"
failed=0
number=0
for step in "${steps[@]}"; do
  number=$((number + 1))
  name="${step%%|*}"
  log="$logs/$(printf '%02d' "$number")-${name// /-}.log"
  printf '[%s] %s ... ' "$number/${#steps[@]}" "$name"
  if bash -c "${step#*|}" > "$log" 2>&1; then
    echo "passed"
  else
    echo "FAILED (see $log)"
    failed=1
    break
  fi
done

echo "Revision: $(git rev-parse --short HEAD)$(git diff --quiet HEAD 2>/dev/null || echo ' plus uncommitted changes'); logs: $logs/"
if [[ "$failed" -ne 0 ]]; then
  echo "Local gate failed at the step above; later steps did not run."
  exit 1
fi
if [[ "$live" == true ]]; then
  echo "Outstanding: the live journey (e2e/AGENTS.md). The gate is not complete until it has run."
  exit 4
fi
echo "Local '$tier' gate passed. Cross-architecture image builds are left to Jenkins."
