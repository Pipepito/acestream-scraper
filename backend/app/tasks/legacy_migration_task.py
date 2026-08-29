"""
One-off background task: copy the EPG programs left over from a v1 -> v2
migration (see ``migrate_database.DatabaseMigrator``).

Scheduled from ``main.lifespan()`` when ``acestream.db.migration.json`` records
pending work, so the dashboard is reachable while the (potentially large)
``epg_programs`` table is copied in batches.
"""
import logging

from app.services.task_service import task_service

logger = logging.getLogger("legacy_migration_task")

TASK_ID = "v1_epg_programs_migration"


def run_v1_epg_programs_migration():
    from migrate_database import DatabaseMigrator

    migrator = DatabaseMigrator()
    last_logged = {"percent": -100.0}

    def report(snapshot):
        task_service.update_task_progress(TASK_ID, snapshot)
        # Throttle log lines to every 5% so a multi-million-row table does not flood the log.
        if snapshot["percent"] - last_logged["percent"] >= 5 or snapshot["processed"] >= snapshot["total"]:
            last_logged["percent"] = snapshot["percent"]
            logger.info(
                "v1 EPG programs migration progress processed=%s/%s migrated=%s skipped=%s percent=%s",
                snapshot["processed"], snapshot["total"], snapshot["migrated"], snapshot["skipped"], snapshot["percent"],
            )

    logger.info("v1 EPG programs migration starting state=%s", migrator.deferred_programs_state() and {
        key: value for key, value in migrator.deferred_programs_state().items() if key != "epg_channel_ids"
    })
    summary = migrator.run_deferred_migration(progress=report, stop_event=task_service.shutdown_event)
    if summary["status"] == "interrupted":
        logger.warning("v1 EPG programs migration interrupted by shutdown; will resume on next start summary=%s", summary)
    else:
        logger.info("v1 EPG programs migration finished summary=%s", summary)
    return summary
