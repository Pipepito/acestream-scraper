"""Track interactive jobs without replacing their scheduled counterparts."""
import asyncio
import inspect
from datetime import datetime, timezone
from starlette.concurrency import run_in_threadpool
from app.services.task_service import task_service


def _summary(kind, result):
    if kind == 'url_scraping':
        rows = result if isinstance(result, list) else [result]
        return {'processed': len(rows), 'failures': sum(str(status).lower().startswith('error') for _, status in rows),
                'channels': sum(len(channels) for channels, _ in rows)}
    if kind == 'epg_refresh':
        rows = result if isinstance(result, list) else [result]
        successful = sum(bool(row.get('success')) for row in rows)
        return {'sources': len(rows), 'successful': successful, 'failed': len(rows) - successful}
    rows = result if isinstance(result, list) else [result]
    return {'checked': sum(row['status'] != 'skipped' for row in rows),
            'skipped': sum(row['status'] == 'skipped' for row in rows),
            'online': sum(row['status'] != 'skipped' and row['is_online'] for row in rows)}


async def run_manual_job(kind, func, *args):
    """Retain the latest-started manual run per family, even if calls overlap."""
    job_id = f'manual_{kind}'
    state = {'task_name': job_id, 'last_run': datetime.now(timezone.utc),
             'next_run': None, 'status': 'running', 'last_error': None,
             'last_result': None, 'progress': None}
    await asyncio.to_thread(task_service.set_manual_state, job_id, state)
    await asyncio.to_thread(task_service.persist_current_state, job_id, state)
    try:
        if inspect.iscoroutinefunction(func):
            result = await func(*args)
        else:
            result = await run_in_threadpool(func, *args)
        state['last_result'] = _summary(kind, result)
        state['status'] = 'idle'
        return result
    except asyncio.CancelledError:
        state['status'] = 'interrupted'
        state['last_error'] = 'Manual run was interrupted'
        raise
    except Exception:
        state['status'] = 'error'
        state['last_error'] = 'Manual run failed; see application logs for details'
        raise
    finally:
        await asyncio.to_thread(task_service.persist_current_state, job_id, state)


async def scrape_batch(service, urls):
    return [await service.scrape_url(url, url_type) for url, url_type in urls]


def refresh_epg_batch(service, source_ids):
    return [service.refresh_source(source_id) for source_id in source_ids]
