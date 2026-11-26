"""Validate the real component catalogue with isolated browsers and local HTTP.

No application backend or production data. Includes keyboard/state regressions,
both themes, narrow reflow, axe, reduced motion and downloadable-logo hashes.
"""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--axe', type=Path, required=True)
args = parser.parse_args()
base = args.base_url.rstrip('/') + '/'
assert urlsplit(base).hostname in {'127.0.0.1', 'localhost'}
args.output.mkdir(parents=True, exist_ok=True)
report = {'layouts': [], 'axe': [], 'checks': [], 'errors': []}


def check(name, condition):
    report['checks'].append({'name': name, 'passed': bool(condition)})


for asset in json.loads((ROOT / 'assets/zztreams/provenance.json').read_text())['files']:
    check('asset hash: ' + asset['file'], hashlib.sha256((ROOT / asset['file']).read_bytes()).hexdigest() == asset['sha256'])

try:
    with sync_playwright() as pw:
        for engine in ['chromium', 'firefox', 'webkit']:
            browser = getattr(pw, engine).launch()
            context = browser.new_context(reduced_motion='reduce', service_workers='block')
            context.add_init_script(path=str(args.axe.resolve()))

            def guard(route):
                if route.request.url.startswith(base) and route.request.method == 'GET':
                    route.continue_()
                else:
                    report['errors'].append('Unexpected request: ' + route.request.url)
                    route.abort()

            context.route('**/*', guard)
            page = context.new_page()
            page.on('pageerror', lambda error: report['errors'].append(str(error)))
            page.on('console', lambda message: report['errors'].append(message.text) if message.type in ['error', 'warning'] else None)
            page.on('response', lambda response: report['errors'].append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
            for width in [320, 390, 820, 1440] if engine == 'chromium' else [390]:
                page.set_viewport_size({'width': width, 'height': 844 if width < 600 else 900})
                for theme in ['dark', 'light']:
                    page.goto(base + 'components.html', wait_until='networkidle')
                    page.evaluate('document.fonts.ready')
                    page.evaluate("async () => { document.querySelectorAll('img').forEach(i => i.loading='eager'); await Promise.all([...document.images].map(i=>i.decode().catch(()=>{}))); }")
                    if theme == 'light':
                        page.locator('#theme-toggle').click()
                    label = f'{engine}-{theme}-{width}'
                    layout = page.evaluate(
                        """() => ({overflow:document.documentElement.scrollWidth>innerWidth+1,h1:document.querySelectorAll('h1').length,main:document.querySelectorAll('main').length,missing:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.src),clipped:[...document.querySelectorAll('button')].filter(e=>e.getClientRects().length&&e.scrollWidth>e.clientWidth+2).map(e=>e.outerHTML),motion:getComputedStyle(document.querySelector('.ds-spinner')).animationName})"""
                    )
                    report['layouts'].append({'case': label, **layout})
                    check(label + ': reflow', not layout['overflow'] and not layout['clipped'] and not layout['missing'] and layout['h1'] == 1 and layout['main'] == 1)
                    check(label + ': reduced motion', layout['motion'] == 'none')
                    if engine == 'chromium':
                        violations = page.evaluate("async () => (await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}})).violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))")
                        report['axe'].append({'case': label, 'violations': violations})
                        check(label + ': axe', not violations)
                    if width in [390, 1440] and engine == 'chromium':
                        page.screenshot(path=str(args.output / (label + '.png')))
                        page.locator('#selection').screenshot(path=str(args.output / (label + '-selection.png')))
                        page.locator('#actions').screenshot(path=str(args.output / (label + '-actions.png')))

            # Exercise each family on a fresh desktop viewport, then modal reflow on phone.
            page.set_viewport_size({'width': 1440, 'height': 900})
            page.goto(base + 'components.html', wait_until='networkidle')
            check(engine + ': mixed checkbox', page.locator('#select-all').evaluate('(e)=>e.indeterminate'))
            page.locator('#select-all').check()
            expect(page.locator('#selection-status')).to_have_text('2 of 2 available channels selected.')
            page.locator('.channel-check').first.uncheck()
            check(engine + ': parent becomes mixed', page.locator('#select-all').evaluate('(e)=>e.indeterminate'))
            page.get_by_label('Compatible MP4', exact=True).check()
            expect(page.get_by_label('Original stream', exact=True)).not_to_be_checked()
            page.locator('#compact-switch').focus()
            page.keyboard.press('Space')
            expect(page.locator('#compact-switch')).to_have_attribute('aria-checked', 'true')
            expect(page.locator('#density-preview')).to_have_class('density-preview compact')
            page.get_by_text('Week', exact=True).click()
            expect(page.locator('#view-status')).to_have_text('Week view selected.')
            page.locator('#sports-chip').click()
            expect(page.locator('#sports-chip')).to_have_attribute('aria-pressed', 'true')
            page.get_by_role('button', name='Remove English filter').focus()
            page.keyboard.press('Delete')
            expect(page.locator('#input-chip-status')).to_have_text('1 filters selected.')
            expect(page.get_by_role('button', name='Remove HD filter')).to_be_focused()
            page.locator('#restore-chips').click()
            expect(page.locator('[data-remove-chip]')).to_have_count(2)
            page.locator('#number-demo').fill('7')
            expect(page.locator('#number-demo')).to_have_attribute('aria-invalid', 'false')
            page.locator('#channel-notes').fill('Example note')
            expect(page.locator('#notes-count')).to_have_text('12 of 160 characters.')
            page.locator('#suggestion-chip').click()
            expect(page.locator('#search-count')).to_have_text('1 example channel.')
            page.locator('#component-search').fill('unmatched')
            expect(page.locator('#search-empty')).to_be_visible()
            page.locator('#clear-search').click()
            expect(page.locator('#search-count')).to_have_text('3 example channels.')
            page.locator('#volume-demo').focus()
            page.keyboard.press('ArrowRight')
            expect(page.locator('#volume-value')).to_have_text('45%')
            page.locator('#range-start').focus()
            page.keyboard.press('End')
            expect(page.locator('#range-status')).to_have_text('Choose an end hour after the start hour.')
            page.keyboard.press('Home')
            expect(page.locator('#range-start')).to_have_attribute('aria-invalid', 'false')
            page.locator('#tab-overview').focus()
            page.keyboard.press('ArrowRight')
            expect(page.locator('#tab-guide')).to_be_focused()
            expect(page.locator('#panel-overview')).to_be_visible()
            page.keyboard.press('Enter')
            expect(page.locator('#panel-guide')).to_be_visible()
            expect(page.locator('#panel-overview')).to_be_hidden()
            page.keyboard.press('End')
            page.keyboard.press('Space')
            expect(page.locator('#panel-sources')).to_be_visible()
            page.locator('#menu-trigger').focus()
            page.keyboard.press('ArrowDown')
            expect(page.get_by_role('menuitem', name='Record now', exact=True)).to_be_focused()
            page.keyboard.press('End')
            page.keyboard.press('Enter')
            expect(page.locator('#schedule-menu')).to_be_visible()
            page.keyboard.press('Home')
            page.keyboard.press('Enter')
            expect(page.locator('#action-result')).to_have_text('Record now selected.')
            expect(page.locator('#menu-trigger')).to_be_focused()
            page.locator('#menu-trigger').click()
            page.keyboard.press('Escape')
            expect(page.locator('#schedule-menu')).to_be_hidden()
            page.locator('#icon-favorite').focus()
            expect(page.locator('#favorite-tip')).to_be_visible()
            page.keyboard.press('Escape')
            expect(page.locator('#favorite-tip')).to_be_hidden()
            page.locator('#snackbar-demo').click()
            expect(page.locator('#snackbar-demo')).to_be_focused()
            expect(page.locator('#following-snackbar')).to_be_visible()
            page.clock.install()
            page.clock.fast_forward(60_000)
            expect(page.locator('#following-snackbar')).to_be_visible()
            page.keyboard.press('Alt+g')
            expect(page.locator('#snackbar-undo')).to_be_focused()
            page.keyboard.press('Enter')
            expect(page.locator('#following-state')).to_have_text('Northlight restored to Following.')
            expect(page.locator('#snackbar-demo')).to_be_focused()
            page.locator('#advance-progress').click()
            expect(page.locator('#progress-demo')).to_have_attribute('value', '60')
            page.locator('#next-page').click()
            page.locator('#next-page').click()
            expect(page.locator('#next-page')).to_be_disabled()
            page.locator('#previous-page').click()
            expect(page.locator('#page-count')).to_have_text('Page 2 of 3')
            page.locator('[data-destination=Events]').click()
            expect(page.locator('#nav-context')).to_have_text('Events')
            page.locator('#carousel-next').click()
            expect(page.get_by_role('link', name='Racing events mockup')).to_be_in_viewport()
            check(engine + ': carousel scrolls', page.locator('#category-carousel').evaluate('(e)=>e.scrollLeft') > 0)
            for dialog_id in ['details-sheet', 'add-sheet', 'navigation-sheet', 'confirm-sheet', 'schedule-sheet']:
                opener = page.locator(f'[data-open="{dialog_id}"]').first
                opener.click()
                dialog = page.locator('#' + dialog_id)
                expect(dialog).to_be_visible()
                check(engine + ': ' + dialog_id + ' contains focus', dialog.evaluate('(e)=>e.contains(document.activeElement)'))
                controls = dialog.locator('button:not(:disabled),a[href],input:not(:disabled),select')
                controls.last.focus()
                page.keyboard.press('Tab')
                expect(controls.first).to_be_focused()
                page.keyboard.press('Shift+Tab')
                expect(controls.last).to_be_focused()
                page.keyboard.press('Escape')
                expect(dialog).to_be_hidden()
                expect(opener).to_be_focused()
            page.locator('[data-open=schedule-sheet]').last.click()
            page.locator('#schedule-date').fill('2026-11-12')
            page.locator('#schedule-time').fill('21:30')
            page.locator('#schedule-zone').select_option(label='UTC')
            page.get_by_role('button', name='Use this time').click()
            expect(page.locator('#schedule-result')).to_contain_text('2026-11-12 · 21:30 · UTC')
            page.set_viewport_size({'width': 390, 'height': 844})
            page.locator('[data-open=details-sheet]').first.click()
            check(engine + ': phone sheet reflow', page.locator('#details-sheet').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1&&e.getBoundingClientRect().right<=innerWidth+1'))
            page.screenshot(path=str(args.output / (engine + '-mobile-sheet.png')))
            page.keyboard.press('Escape')
            check(engine + ': interactive families passed', True)
            browser.close()
except Exception as error:
    report['errors'].append(str(error))
finally:
    report['failed_checks'] = [item['name'] for item in report['checks'] if not item['passed']]
    (args.output / 'component-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'checks': len(report['checks']), 'layouts': len(report['layouts']), 'axe': len(report['axe']), 'failed_checks': report['failed_checks'], 'errors': report['errors']}, indent=2))
raise SystemExit(bool(report['failed_checks'] or report['errors']))
