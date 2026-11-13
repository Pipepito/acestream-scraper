"""Check the deployed static brand surface under a repository base path.

Uses the local HTTP preview, isolated Chromium and bundled axe. Never uses an
installation, browser profile, remote asset or production data. Output is private.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', required=True)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--axe', required=True, type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
base = args.base_url.rstrip('/') + '/'
assert urlsplit(base).hostname in ('127.0.0.1', 'localhost'), 'Use an isolated local preview'
report = dict(layouts=[], checks={}, axe=[], errors=[], console=[], requests=[], assets=[])


def check(name, value):
    report['checks'][name] = bool(value)


manifest = json.loads((ROOT / 'assets/sportzz/asset-map.json').read_text())
for asset in manifest['files']:
    path = ROOT / asset['file']
    check('asset_hash:' + asset['file'], hashlib.sha256(path.read_bytes()).hexdigest() == asset['sha256'])

for asset in json.loads((ROOT / 'assets/zztreams/provenance.json').read_text())['files']:
    check('current_logo_hash:' + asset['file'], hashlib.sha256((ROOT / asset['file']).read_bytes()).hexdigest() == asset['sha256'])

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    context = browser.new_context(service_workers='block', reduced_motion='reduce')
    context.add_init_script(path=str(args.axe.resolve()))

    def guard(route):
        if route.request.url.startswith(base) and route.request.method == 'GET':
            route.continue_()
        else:
            report['requests'].append(route.request.url)
            route.abort()

    context.route('**/*', guard)
    page = context.new_page()
    page.on('pageerror', lambda e: report['errors'].append(str(e)))
    page.on('console', lambda m: report['console'].append(m.text) if m.type in ('error', 'warning') else None)
    page.on('response', lambda r: report['errors'].append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)

    def go(path):
        page.goto(urljoin(base, path), wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        page.evaluate("""async () => {
            document.querySelectorAll('img[loading=lazy]').forEach(i => i.loading='eager');
            await Promise.all([...document.images].map(i => i.decode().catch(() => {})));
        }""")

    for width in [320, 390, 820, 1440]:
        page.set_viewport_size(dict(width=width, height=844 if width < 600 else 900))
        for theme in ['dark', 'light']:
            go('brand-system.html')
            if theme == 'light':
                page.locator('#theme-toggle').click()
            label = f'brand-{theme}-{width}'
            result = page.evaluate("""() => ({
                overflow: document.documentElement.scrollWidth > innerWidth + 1,
                missing: [...document.images].filter(i => !i.naturalWidth).map(i => i.src),
                headings: document.querySelectorAll('h1').length,
                ratios: [...document.querySelectorAll('[data-ratio]')].map(e => e.textContent),
                tokens: Object.fromEntries(['--accent','--surface','--text','--display','--radius-control'].map(k => [k,getComputedStyle(document.body).getPropertyValue(k).trim()])),
                motion: getComputedStyle(document.querySelector('.button')).transitionDuration
            })""")
            report['layouts'].append(dict(case=label, **result))
            check(label + ':layout', not result['overflow'] and not result['missing'] and result['headings'] == 1)
            check(label + ':uppercase_identity', page.locator('.sportzz-wordmark:visible').get_attribute('alt') == 'ZZSTREAMS')
            check(label + ':contrast', all('AA normal text' in s for s in result['ratios']))
            check(label + ':reduced_motion', result['motion'] == '0s')
            axe = page.evaluate("""async () => {
                const r = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});
                return {violations:r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,count:v.nodes.length}))};
            }""")
            report['axe'].append(dict(case=label, **axe))
            if width in [390, 820, 1440]:
                page.screenshot(path=str(args.output / (label + '.png')))
            if width == 1440:
                for section in ['identity', 'color', 'components']:
                    page.locator('#' + section).screenshot(path=str(args.output / f'brand-{theme}-{section}.png'))
            # Shared tokens and real controls must agree with the reference.
            reference_tokens = result['tokens']
            go('workflow-prototype.html?screen=dashboard&theme=' + theme)
            tokens = page.evaluate("""() => Object.fromEntries(['--accent','--surface','--text','--display','--radius-control'].map(k=>[k,getComputedStyle(document.body).getPropertyValue(k).trim()]))""")
            check(label + ':mockup_tokens', tokens == reference_tokens)
            check(label + ':mockup_overflow', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
            if width in [390, 820, 1440]:
                page.screenshot(path=str(args.output / f'watch-{theme}-{width}.png'))

    for preset, expected in [('cyan', 'rgb(46, 230, 214)'), ('lime', 'rgb(182, 255, 0)'), ('coral', 'rgb(255, 173, 135)')]:
        for theme in ['light', 'dark']:
            go(f'workflow-prototype.html?screen=dashboard&preset={preset}&theme={theme}')
            color = page.locator('.hero-copy .button.primary').evaluate('e => getComputedStyle(e).backgroundColor')
            check(f'preset-accent:{preset}:{theme}', color == expected)

    page.set_viewport_size(dict(width=1440, height=900))
    go('brand-system.html')
    page.keyboard.press('Tab')
    check('skip_first', page.locator(':focus').get_attribute('class') == 'skip')
    check('focus_visible', page.locator(':focus').evaluate("e => getComputedStyle(e).outlineStyle !== 'none'"))
    page.keyboard.press('Enter')
    check('skip_main', page.locator(':focus').get_attribute('id') == 'main')
    page.locator('#open-dialog').click()
    check('dialog_initial_focus', page.locator(':focus').get_attribute('id') == 'dialog-cancel')
    page.keyboard.press('Shift+Tab')
    check('dialog_focus_trap', page.locator(':focus').get_attribute('id') == 'dialog-save')
    page.keyboard.press('Escape')
    check('dialog_escape_return', not page.locator('dialog').is_visible() and page.locator(':focus').get_attribute('id') == 'open-dialog')
    page.locator('#open-dialog').click()
    page.locator('#dialog-save').click()
    check('dialog_confirm', 'confirmed' in page.locator('#action-status').inner_text())
    page.locator('[data-filter=tennis]').click()
    check('filter_changes_cards', not page.locator('[data-sport=football]').is_visible() and page.locator('[data-sport=tennis]').is_visible())
    page.locator('#clear-demo').click()
    check('filter_clear', page.locator('[data-sport=football]').is_visible())
    page.locator('#favorite-demo').click()
    check('favorite_pressed', page.locator('#favorite-demo').get_attribute('aria-pressed') == 'true')
    page.locator('#example-number').fill('2')
    check('valid_field', page.locator('#example-number').get_attribute('aria-invalid') == 'false')
    page.locator('#example-number').fill('0')
    check('invalid_field', page.locator('#example-number').get_attribute('aria-invalid') == 'true')
    page.locator('#play-demo').click()
    check('play_pause', 'Playing example' in page.locator('#player-status').inner_text())
    page.locator('#play-demo').click()
    check('pause_play', 'Paused example' in page.locator('#player-status').inner_text())
    page.locator('#retry-demo').click()
    check('retry', 'succeeded' in page.locator('#retry-status').inner_text())

    # Deployed local links/assets and page-to-page navigation at the repository base path.
    for name in ['brand-system.html', 'index.html', 'workflow-gallery.html', 'workflow-prototype.html']:
        go(name)
        links = page.locator('[href],[src]').evaluate_all("es => es.map(e => e.href || e.src).filter(Boolean)")
        for link in sorted(set(links)):
            target = urlsplit(link)
            if target.netloc != urlsplit(base).netloc:
                continue
            response = context.request.get(link.split('#')[0])
            check('link:' + target.path, response.ok)
            if target.fragment and target.path == urlsplit(page.url).path:
                check('anchor:' + name + '#' + target.fragment, page.locator('[id="' + target.fragment + '"]').count() == 1)
        if name != 'brand-system.html':
            page.get_by_role('link', name='Brand system', exact=True).first.click()
            check(name + ':brand_navigation', page.url.endswith('/brand-system.html'))
    go('brand-system.html')
    page.get_by_role('link', name='Mockups', exact=True).click()
    check('reference_to_mockup', 'workflow-prototype.html' in page.url)
    go('workflow-prototype.html?screen=recording-settings&theme=light')
    page.screenshot(path=str(args.output / 'settings-light-desktop.png'))
    browser.close()

report['summary'] = dict(passed=sum(report['checks'].values()), failed=sum(not v for v in report['checks'].values()), axe_violations=sum(len(r['violations']) for r in report['axe']), errors=len(report['errors']), console=len(report['console']), unexpected_requests=len(report['requests']))
(args.output / 'brand-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['summary'], indent=2))
raise SystemExit(any(v for k,v in report['summary'].items() if k != 'passed'))
