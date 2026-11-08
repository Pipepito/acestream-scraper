#!/usr/bin/env python3
"""Compare two owned builds with identical 10,000-channel synthetic inventories.

Only browser drafts change. Cancel/Discard must produce zero API writes.
Run after measure-production.py has prepared the independent fixture databases.
"""
import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ('before', 'after'):
        parser.add_argument(f'--{label}-url', required=True)
        parser.add_argument(f'--{label}-revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for url in (args.before_url, args.after_url):
        if urlsplit(url).hostname != '127.0.0.1':
            parser.error('Use isolated loopback backends')
    args.output.mkdir(parents=True, exist_ok=True)
    # The intentionally slow unvirtualized baseline can exceed five seconds on
    # a busy validation host. Record the actual latency; do not cap the measurement.
    expect.set_options(timeout=30_000)
    results, errors, writes = [], [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for run in range(5):
            for label in ('before', 'after'):
                context = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='en-GB')
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda request: writes.append(request.url) if request.method not in ('GET', 'HEAD', 'OPTIONS') else None)
                page.add_init_script("window.__tasks=[]; new PerformanceObserver(l=>window.__tasks.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true})")
                page.goto(getattr(args, f'{label}_url') + '/tv-channels')
                page.wait_for_load_state('networkidle')
                page.evaluate('window.__tasks=[]')
                started = time.perf_counter()
                page.get_by_role('button', name='Reorder channels', exact=True).click()
                first = page.get_by_role('button', name='Drag Synthetic channel 00001', exact=True)
                expect(first).to_be_visible()
                page.wait_for_load_state('networkidle')
                elapsed = (time.perf_counter() - started) * 1000
                measured = page.evaluate("({longTasks:window.__tasks,heap:performance.memory.usedJSHeapSize,dom:document.querySelectorAll('*').length})")
                session = context.new_cdp_session(page)
                measured['cdpHeapOpen'] = session.send('Runtime.getHeapUsage')['usedSize']
                measured['renderedRows'] = page.get_by_role('list', name='Channel order').get_by_role('listitem').count()
                first.focus()
                started = time.perf_counter()
                first.press('ArrowDown')
                expect(page.get_by_role('list', name='Channel order').get_by_role('listitem').nth(1)).to_contain_text('Synthetic channel 00001')
                page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                measured['keyboardMoveMs'] = (time.perf_counter() - started) * 1000
                measured['focusRetained'] = first.evaluate('(element) => element === document.activeElement')
                if label == 'after':
                    assert measured['renderedRows'] < 40
                    assert measured['focusRetained']
                page.get_by_role('button', name='Cancel', exact=True).click()
                page.get_by_role('button', name='Discard changes', exact=True).click()
                expect(page.get_by_role('list', name='Channel order')).to_have_count(0)
                session.send('HeapProfiler.collectGarbage')
                measured['heapAfterCancelAndGC'] = session.send('Runtime.getHeapUsage')['usedSize']
                results.append({'build': label, 'revision': getattr(args, f'{label}_revision'), 'run': run + 1, 'openSettledMs': elapsed, **measured})
                context.close()
                (args.output / 'measurements.json').write_text(json.dumps({'browser': browser.version, 'results': results, 'pageErrors': errors, 'writes': writes}, indent=2) + '\n')
        browser.close()
    assert not errors, errors
    assert not writes, writes
    print(f'{len(results)} alternating samples; no page errors or API writes')


if __name__ == '__main__':
    main()
