"""
Periodic task for scraping URLs.
"""
from app.config.database import SessionLocal
from app.services import notification_service
from app.services.scraper_service import ScraperService
import logging
import asyncio


def run_url_scraping_task(saved_search_targets=None):
    db = SessionLocal()
    logger = logging.getLogger("url_scraping_task")
    try:
        service = ScraperService(db)
        enabled_urls = [(row.url, row.url_type) for row in service.get_enabled_urls()]
        db.rollback()
        logger.info(f"Starting URL scraping task for {len(enabled_urls)} URLs.")

        async def scrape_all():
            processed = 0
            failures = 0
            excluded = 0
            for url, url_type in enabled_urls:
                try:
                    channels, status = await service.scrape_url(url, url_type)
                    processed += 1
                    excluded += service.last_import_exclusions
                    if status.lower().startswith("error"):
                        failures += 1
                    logger.info(
                        "Scraped %s (type: %s): %s, channels found: %s",
                        url,
                        url_type,
                        status,
                        len(channels),
                    )
                except Exception as exc:
                    failures += 1
                    db.rollback()
                    logger.exception("Failed scraping url=%s type=%s error=%s", url, url_type, exc)
            return {
                "processed": processed,
                "failures": failures,
                "import_exclusions": {"excluded_candidates": excluded},
            }

        result = asyncio.run(scrape_all())
        from app.services.catalogue_service import CatalogueService
        catalogues = CatalogueService(db).refresh_enabled()
        if catalogues['catalogues']:
            result.update(catalogues)
            result['processed'] += catalogues['catalogues']
            result['failures'] += catalogues['catalogue_failures']


        from app.services.event_source_service import EventSourceService
        from app.services.task_service import task_service
        result['events'] = EventSourceService(db).refresh_all(shutdown=task_service.shutdown_event)
        from app.services.saved_search_service import run_reserved_batch
        result['saved_searches'] = run_reserved_batch(saved_search_targets or [], task_service.shutdown_event)
        logger.info("URL scraping task completed result=%s", result)
        notification_service.scraping_completed(result)
        return result
    except Exception as exc:
        logger.exception("URL scraping task failed error=%s", exc)
        notification_service.task_failed('url_scraping', exc)
        raise
    finally:
        db.close()
