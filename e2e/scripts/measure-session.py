#!/usr/bin/env python3
"""Measure discarded reorder/filter/scroll cycles on an owned 10,000-row fixture.

Keeps one browser context for thirty cycles. It records precise post-GC heap,
checks virtualized keyboard focus and refuses any API mutation or page error.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    if urlsplit(args.base_url).hostname != '127.0.0.1':
        parser.error('Use an isolated loopback fixture backend')
    args.output.mkdir(parents=True, exist_ok=True)
    rows, errors, writes = [], [], []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: writes.append(request.method)
                if request.method not in ('GET', 'HEAD', 'OPTIONS') else None)
        page.goto(args.base_url + '/tv-channels')
        page.wait_for_load_state('networkidle')
        session = context.new_cdp_session(page)

        def save():
            (args.output / 'measurements.json').write_text(json.dumps({
                'revision': args.revision, 'browser': browser.version,
                'cycles': rows, 'pageErrors': errors, 'writes': writes,
            }, indent=2) + '\n')

        for cycle in range(31):
            session.send('HeapProfiler.collectGarbage')
            rows.append({'cycle': cycle,
                         'heap': session.send('Runtime.getHeapUsage')['usedSize'],
                         'dom': page.locator('*').count()})
            save()
            if cycle == 30:
                break
            page.get_by_role('button', name='Reorder channels', exact=True).click()
            first = page.get_by_role('button', name='Drag Synthetic channel 00001', exact=True)
            expect(first).to_be_visible()
            first.focus()
            first.press('End')
            last = page.get_by_role('button', name='Drag Synthetic channel 10000', exact=True)
            expect(last).to_be_focused()
            last.press('ArrowUp')
            expect(last).to_be_focused()
            page.get_by_role('button', name='Cancel', exact=True).click()
            page.get_by_role('button', name='Discard changes', exact=True).click()
            expect(page.get_by_role('list', name='Channel order')).to_have_count(0)
            search = page.get_by_role('textbox', name='Search', exact=True)
            search.fill('00001')
            expect(page.get_by_role('row').filter(has_text='Synthetic channel 00001')).to_have_count(1)
            search.fill('')
            page.wait_for_load_state('networkidle')
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.evaluate('window.scrollTo(0, 0)')
        assert not errors, errors
        assert not writes, writes
        print('30 same-context reorder/filter/scroll cycles; no errors or writes')
        context.close()
        browser.close()


if __name__ == '__main__':
    main()
