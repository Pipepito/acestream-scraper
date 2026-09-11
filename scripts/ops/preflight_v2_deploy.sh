#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONFIG_DIR="${CONFIG_DIR:-$ROOT_DIR/config}"
BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-}"
SCRAPER_DB_PATH="${SCRAPER_DB_PATH:-}"
LEGACY_DB_PATH="${LEGACY_DB_PATH:-}"
ALLOW_BOTH_DBS=false
DO_BACKUP=true
EXPORT_SOURCES_ON_UNSAFE=true
RESCUE_DB_PATH=""

usage() {
  cat <<'USAGE'
Usage: bash scripts/ops/preflight_v2_deploy.sh [options]

Options:
  --config-dir <path>     Override config directory (default: ./config)
  --backup-dir <path>     Override backup root directory (default: ./config/backups)
  --scraper-db <path>     Override v2 database path (default: <config-dir>/scraper.db)
  --legacy-db <path>      Override legacy database path (default: <config-dir>/acestream.db)
  --allow-both-dbs        Allow deployment when both scraper.db and acestream.db exist
  --no-backup             Skip backup creation (not recommended)
  --no-rescue-export      Do not create rescue DB with scraper sources on UNSAFE result
  --rescue-db <path>      Explicit rescue DB output path for source export
  --help                  Show this help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-dir)
      CONFIG_DIR="$2"
      shift 2
      ;;
    --backup-dir)
      BACKUP_BASE_DIR="$2"
      shift 2
      ;;
    --scraper-db)
      SCRAPER_DB_PATH="$2"
      shift 2
      ;;
    --legacy-db)
      LEGACY_DB_PATH="$2"
      shift 2
      ;;
    --allow-both-dbs)
      ALLOW_BOTH_DBS=true
      shift
      ;;
    --no-backup)
      DO_BACKUP=false
      shift
      ;;
    --no-rescue-export)
      EXPORT_SOURCES_ON_UNSAFE=false
      shift
      ;;
    --rescue-db)
      RESCUE_DB_PATH="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$SCRAPER_DB_PATH" ]]; then
  SCRAPER_DB_PATH="$CONFIG_DIR/scraper.db"
fi
if [[ -z "$LEGACY_DB_PATH" ]]; then
  LEGACY_DB_PATH="$CONFIG_DIR/acestream.db"
fi
if [[ -z "$BACKUP_BASE_DIR" ]]; then
  BACKUP_BASE_DIR="$CONFIG_DIR/backups"
fi

LEGACY_MIGRATED_PATH="${LEGACY_DB_PATH}.migrated"
SQLITE_AVAILABLE=false
if command -v sqlite3 >/dev/null 2>&1; then
  SQLITE_AVAILABLE=true
fi

timestamp="$(date +"%Y%m%d-%H%M%S")"
backup_run_dir="$BACKUP_BASE_DIR/$timestamp"

has_file() {
  [[ -f "$1" ]]
}

backup_file() {
  local src="$1"
  local dst="$2"
  if [[ "$SQLITE_AVAILABLE" == "true" ]]; then
    sqlite3 "$src" ".backup '$dst'"
  else
    cp -p "$src" "$dst"
  fi
}

check_integrity() {
  local db_path="$1"
  local label="$2"

  if [[ "$SQLITE_AVAILABLE" != "true" ]]; then
    echo "  - Integrity: skipped (sqlite3 not found)"
    return 0
  fi

  local check_result
  check_result="$(sqlite3 "$db_path" "PRAGMA quick_check;" 2>/dev/null | head -n 1 || true)"
  if [[ "$check_result" != "ok" ]]; then
    echo "  - Integrity: FAILED (${check_result:-no result})"
    return 1
  fi

  echo "  - Integrity: ok"
  return 0
}

table_count() {
  local db_path="$1"
  local table="$2"
  local exists
  exists="$(sqlite3 "$db_path" "SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='$table';" 2>/dev/null || echo "0")"
  if [[ "$exists" != "1" ]]; then
    echo "-"
    return
  fi
  sqlite3 "$db_path" "SELECT COUNT(1) FROM \"$table\";" 2>/dev/null || echo "?"
}

print_counts() {
  local db_path="$1"

  if [[ "$SQLITE_AVAILABLE" != "true" ]]; then
    echo "  - Table counts: skipped (sqlite3 not found)"
    return
  fi

  local tables=(
    scraped_urls
    acestream_channels
    tv_channels
    epg_sources
    epg_channels
    epg_programs
    epg_string_mappings
    settings
  )

  echo "  - Table counts:"
  for table in "${tables[@]}"; do
    local count
    count="$(table_count "$db_path" "$table")"
    printf "    * %-22s %s\n" "$table" "$count"
  done
}

table_exists() {
  local db_path="$1"
  local table="$2"
  if [[ "$SQLITE_AVAILABLE" != "true" ]]; then
    return 1
  fi
  local exists
  exists="$(sqlite3 "$db_path" "SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='$table';" 2>/dev/null || echo "0")"
  [[ "$exists" == "1" ]]
}

export_scraper_sources_rescue() {
  local output_db="$1"
  if [[ "$SQLITE_AVAILABLE" != "true" ]]; then
    echo "Rescue export skipped: sqlite3 not available."
    return 1
  fi

  mkdir -p "$(dirname "$output_db")"
  rm -f "$output_db"

  sqlite3 "$output_db" <<'SQL'
CREATE TABLE IF NOT EXISTS scraped_urls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL UNIQUE,
  url_type TEXT DEFAULT 'regular',
  status TEXT DEFAULT 'active',
  enabled INTEGER DEFAULT 1,
  added_at TEXT DEFAULT (datetime('now')),
  source_db TEXT
);
SQL

  local source_db
  for source_db in "$SCRAPER_DB_PATH" "$LEGACY_DB_PATH"; do
    if [[ ! -f "$source_db" ]]; then
      continue
    fi
    if ! table_exists "$source_db" "scraped_urls"; then
      continue
    fi

    local source_db_sql
    source_db_sql="${source_db//\'/\'\'}"

    sqlite3 "$output_db" <<SQL
ATTACH DATABASE '$source_db_sql' AS src;
INSERT OR IGNORE INTO scraped_urls (url, url_type, status, enabled, added_at, source_db)
SELECT
  TRIM(url),
  COALESCE(NULLIF(url_type, ''), 'regular'),
  COALESCE(NULLIF(status, ''), 'active'),
  COALESCE(enabled, 1),
  COALESCE(added_at, datetime('now')),
  '$source_db_sql'
FROM src.scraped_urls
WHERE url IS NOT NULL AND TRIM(url) <> '';
DETACH DATABASE src;
SQL
  done

  local exported_count
  exported_count="$(sqlite3 "$output_db" "SELECT COUNT(1) FROM scraped_urls;" 2>/dev/null || echo "0")"
  if [[ "$exported_count" == "0" ]]; then
    rm -f "$output_db"
    echo "Rescue export completed but no scraper sources were found."
    return 1
  fi

  echo "$exported_count"
  return 0
}

echo "== Acestream Scraper v2 Deploy Preflight =="
echo "Root: $ROOT_DIR"
echo "Config dir: $CONFIG_DIR"
echo "v2 DB: $SCRAPER_DB_PATH"
echo "Legacy DB: $LEGACY_DB_PATH"
echo "Legacy marker: $LEGACY_MIGRATED_PATH"
echo

scraper_exists=false
legacy_exists=false
marker_exists=false
if has_file "$SCRAPER_DB_PATH"; then scraper_exists=true; fi
if has_file "$LEGACY_DB_PATH"; then legacy_exists=true; fi
if has_file "$LEGACY_MIGRATED_PATH"; then marker_exists=true; fi

echo "Detected files:"
echo "  - scraper.db: $scraper_exists"
echo "  - acestream.db: $legacy_exists"
echo "  - acestream.db.migrated: $marker_exists"
echo

if [[ "$DO_BACKUP" == "true" ]]; then
  mkdir -p "$backup_run_dir"
  echo "Creating backups in: $backup_run_dir"

  if [[ "$scraper_exists" == "true" ]]; then
    backup_file "$SCRAPER_DB_PATH" "$backup_run_dir/scraper.db"
    echo "  - Backed up scraper.db"
  fi
  if [[ "$legacy_exists" == "true" ]]; then
    backup_file "$LEGACY_DB_PATH" "$backup_run_dir/acestream.db"
    echo "  - Backed up acestream.db"
  fi
  if [[ "$marker_exists" == "true" ]]; then
    backup_file "$LEGACY_MIGRATED_PATH" "$backup_run_dir/acestream.db.migrated"
    echo "  - Backed up acestream.db.migrated"
  fi
  echo
else
  echo "WARNING: backups skipped (--no-backup)"
  echo
fi

integrity_failures=0
if [[ "$scraper_exists" == "true" ]]; then
  echo "scraper.db checks:"
  if ! check_integrity "$SCRAPER_DB_PATH" "scraper.db"; then
    integrity_failures=$((integrity_failures + 1))
  fi
  print_counts "$SCRAPER_DB_PATH"
  echo
fi

if [[ "$legacy_exists" == "true" ]]; then
  echo "acestream.db checks:"
  if ! check_integrity "$LEGACY_DB_PATH" "acestream.db"; then
    integrity_failures=$((integrity_failures + 1))
  fi
  print_counts "$LEGACY_DB_PATH"
  echo
fi

status="SAFE"
reason=""

if [[ "$integrity_failures" -gt 0 ]]; then
  status="UNSAFE"
  reason="Database integrity check failed."
elif [[ "$legacy_exists" == "true" && "$scraper_exists" == "true" && "$marker_exists" == "false" && "$ALLOW_BOTH_DBS" != "true" ]]; then
  status="UNSAFE"
  reason="Both v2 and legacy databases are present without migration marker. This can cause confusing merge behavior on startup."
elif [[ "$legacy_exists" == "true" && "$scraper_exists" == "false" ]]; then
  reason="Legacy-only state detected. First v2 startup should migrate and archive legacy DB."
elif [[ "$legacy_exists" == "false" && "$scraper_exists" == "true" ]]; then
  reason="v2 database detected. Deployment should reuse existing data."
elif [[ "$legacy_exists" == "false" && "$scraper_exists" == "false" ]]; then
  reason="No existing database files detected. Fresh install state."
else
  reason="Post-migration or mixed state detected with explicit override."
fi

echo "== Preflight Result =="
echo "Status: $status"
echo "Reason: $reason"
echo

if [[ "$status" == "UNSAFE" ]]; then
  rescue_db_target="$RESCUE_DB_PATH"
  if [[ -z "$rescue_db_target" ]]; then
    rescue_db_target="$backup_run_dir/scraper_sources_rescue.db"
  fi

  rescue_created=false
  rescue_count=0
  if [[ "$EXPORT_SOURCES_ON_UNSAFE" == "true" ]]; then
    if rescue_count="$(export_scraper_sources_rescue "$rescue_db_target")"; then
      rescue_created=true
    fi
  fi

  echo "Action required before deployment:"
  if [[ "$DO_BACKUP" == "true" ]]; then
    echo "  1. Keep backups from: $backup_run_dir"
  else
    echo "  1. Create manual DB backups before any migration/deploy step."
  fi
  if [[ "$rescue_created" == "true" ]]; then
    echo "  2. Rescue DB created with scraper sources: $rescue_db_target ($rescue_count sources)"
    echo "     Use this file to recover source URLs into a clean v2 database."
  elif [[ "$EXPORT_SOURCES_ON_UNSAFE" == "true" ]]; then
    echo "  2. Rescue DB was not created (no sources found or sqlite unavailable)."
  else
    echo "  2. Rescue export skipped (--no-rescue-export)."
  fi
  echo "  3. Ensure only one active source of truth before startup:"
  echo "     - keep scraper.db as active v2 DB, or"
  echo "     - keep acestream.db (legacy) and let one-time migration run"
  echo "  4. Re-run this preflight script until Status is SAFE"
  exit 1
fi

echo "Safe to deploy v2."
echo "Recommended: keep backup folder until post-deploy validation is complete."
