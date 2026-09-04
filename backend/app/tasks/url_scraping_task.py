"""
Periodic task for scraping URLs.
"""
from app.config.database import SessionLocal
from app.services.scraper_service import ScraperService
import logging
import asyncio


def run_url_scraping_task():
    db = SessionLocal()
    logger = logging.getLogger("url_scraping_task")
    try:
        service = ScraperService(db)
        enabled_urls = service.get_enabled_urls()
        logger.info(f"Starting URL scraping task for {len(enabled_urls)} URLs.")

        async def scrape_all():
            processed = 0
            failures = 0
            for url_obj in enabled_urls:
                try:
                    channels, status = await service.scrape_url(url_obj.url, url_obj.url_type)
                    processed += 1
                    if status.lower().startswith("error"):
                        failures += 1
                    logger.info(
                        "Scraped %s (type: %s): %s, channels found: %s",
                        url_obj.url,
                        url_obj.url_type,
                        status,
                        len(channels),
                    )
                except Exception as exc:
                    failures += 1
                    logger.exception("Failed scraping url=%s type=%s error=%s", url_obj.url, url_obj.url_type, exc)
            return {
                "processed": processed,
                "failures": failures,
            }

        result = asyncio.run(scrape_all())
        logger.info("URL scraping task completed result=%s", result)
        return result
    except Exception as exc:
        logger.exception("URL scraping task failed error=%s", exc)
        raise
    finally:
        db.close()
