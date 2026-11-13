#!/usr/bin/env python3
"""Measure a built SPA against an explicitly isolated loopback fixture backend.

Never use a live installation: this provisions access/setup and synthetic inventory.
The caller must provide its temporary SQLite database and a temporary output folder.
"""
import argparse
import json
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if urlsplit(args.base_url).hostname != '127.0.0.1' or '/tmp/' not in str(args.database.resolve()):
        parser.error('Use an owned 127.0.0.1 backend with a temporary database')
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='en-GB')
        request = context.request
        status = request.get(args.base_url + '/api/v1/auth/status').json()
        if status['mode'] == 'pending':
            response = request.post(args.base_url + '/api/v1/auth/bootstrap', data={
                'enabled': False, 'username': 'fixture', 'password': 'unused', 'password_confirmation': 'unused'},
                headers={'X-CSRF-Token': status['csrf']})
            assert response.ok, response.text()
        setup = request.get(args.base_url + '/api/v1/setup').json()
        response = request.put(args.base_url + '/api/v1/setup', data={
            'expected_revision': setup['revision'], 'runtime': setup['runtime'], 'setup_complete': True})
        assert response.ok, response.text()
        context.close()
        for size in (100, 10000):
            with sqlite3.connect(args.database) as db:
                db.executemany("INSERT OR IGNORE INTO tv_channels (id,name,category,is_active,is_favorite,created_at,updated_at) VALUES (?,?,'Test',1,0,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)",
                               [(n, f'Synthetic channel {n:05d}') for n in range(1, size + 1)])
            for route in ('/', '/settings', '/tv-channels', '/live-tv', '/scraper/builder'):
                for run in range(5):
                    context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='en-GB')
                    page = context.new_page()
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.add_init_script("window.__longTasks=[]; new PerformanceObserver(l=>window.__longTasks.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true})")
                    for cache in ('cold', 'warm'):
                        started = time.perf_counter()
                        page.goto(args.base_url + route)
                        page.locator('main h1').first.wait_for()
                        page.wait_for_load_state('networkidle')
                        measurements = page.evaluate("""() => ({title: document.querySelector('main h1')?.textContent,
                            resources: performance.getEntriesByType('resource').map(r=>({name: new URL(r.name).pathname, initiator:r.initiatorType, transfer:r.transferSize, decoded:r.decodedBodySize, duration:r.duration})),
                            longTasks:window.__longTasks, heap:performance.memory?.usedJSHeapSize,
                            navigation:performance.getEntriesByType('navigation')[0].toJSON()})""")
                        results.append({'catalogueSize':size,'route':route,'run':run+1,'cache':cache,'settledMs':round((time.perf_counter()-started)*1000),**measurements})
                    if run == 0:
                        page.screenshot(path=str(args.output / f'{size}-{route.strip("/").replace("/", "-") or "watch"}.png'), full_page=True)
                    context.close()
            (args.output / 'measurements.json').write_text(json.dumps({'revision':args.revision,'browser':browser.version,'results':results,'pageErrors':errors}, indent=2))
        browser.close()
    if errors:
        raise RuntimeError(f'{len(errors)} browser errors; inspect measurements.json')


if __name__ == '__main__':
    main()
