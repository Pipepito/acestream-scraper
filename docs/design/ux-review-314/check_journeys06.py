"""Connected design journey checks; synthetic local state only."""

import argparse
import json
import mimetypes
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, unquote, urlencode
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('--output', required=True)
a = ap.parse_args()
out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
report = {'checks': {}, 'errors': [], 'blocked': []}


def check(name, value):
    report['checks'][name] = bool(value)


with sync_playwright() as p:
    b = p.chromium.launch()
    c = b.new_context(service_workers='block', reduced_motion='reduce')

    def intercept(r):
        u = urlsplit(r.request.url)
        f = (ROOT / unquote(u.path).lstrip('/')).resolve()
        if u.hostname != 'design.invalid' or r.request.method != 'GET' or not f.is_relative_to(ROOT) or not f.is_file():
            report['blocked'].append(u.path)
            r.abort()
            return
        r.fulfill(body=f.read_bytes(), content_type=mimetypes.guess_type(f.name)[0] or 'text/plain')

    c.route('**/*', intercept)
    page = c.new_page()
    page.on('pageerror', lambda e: report['errors'].append(str(e)))
    for preset in ['lime', 'coral', 'cyan']:

        def go(sid):
            page.goto('http://design.invalid/workflow-prototype.html?' + urlencode(dict(screen=sid, preset=preset, review=1)))
            page.evaluate('document.fonts.ready')

        def nav(sid):
            page.locator('main [data-screen="' + sid + '"]').first.click()

        go('dashboard')
        check(preset + '_seven_destinations', page.locator('.study-layout>.sidebar nav a').count() == 7)
        page.locator('.watch-hero [data-action=watch]').click()
        check(preset + '_watch_connected', page.evaluate('__workflow.current') == 'live' and page.evaluate('__workflow.playback.active'))
        page.locator('#f-live-q').fill('Northlight')
        owner = page.evaluate('__workflow.playback.owner')
        page.locator('#state-select').select_option('refreshing')
        check(preset + '_refresh_keeps_owner', page.evaluate('__workflow.playback.owner') == owner)
        nav('recording-schedule')
        check(preset + '_record_exact_times', not page.locator('#f-recording-adjust_times').is_checked() and page.locator('#f-recording-start_time').input_value() == '2026-11-08T20:00')
        go('recordings')
        nav('recording-settings')
        check(preset + '_settings_beside_recordings', page.evaluate('__workflow.current') == 'recording-settings')
        go('channels')
        nav('add-channels')
        nav('source-web')
        check(preset + '_source_setup_connected', page.evaluate('__workflow.current') == 'source-web')
        command = page.locator('#form-source [data-action=command]')
        check(preset + '_find_channels_is_primary', command.get_attribute('class').endswith('primary'))
        page.locator('#f-source-url').fill('')
        check(preset + '_empty_source_blocks_find', command.is_disabled())
        page.locator('#f-source-url').fill('https://example.invalid/household')
        command.click()
        check(preset + '_saved_then_queued_no_discard', page.evaluate('__workflow.current') == 'source-results' and not page.locator('#confirm').is_visible())
        nav('setup-guide')
        check(preset + '_guide_reuses_editor', page.evaluate('__workflow.current') == 'guide-source')
        nav('guide-match')
        check(preset + '_guide_review_connected', page.locator('[data-action=apply-choice]').is_disabled())
        go('connections')
        nav('casting')
        nav('remote-player')
        check(preset + '_device_purpose_group', page.evaluate('__workflow.current') == 'remote-player')
        go('settings')
        nav('access-account')
        page.locator('#f-account-administrator').check()
        check(preset + '_access_dependencies', page.locator('#f-permissions-live').is_disabled())
        go('system')
        nav('jobs')
        nav('job-detail')
        check(preset + '_problem_to_history', page.evaluate('__workflow.current') == 'job-detail')
        go('source-web')
        page.locator('form details').evaluate('(e)=>e.open=true')
        page.locator('#f-source-scrape_bare_ids').check()
        check(preset + '_advanced_custom_indicator', 'custom active' in page.locator('[data-advanced-status]').inner_text())
        page.locator('#preset-select').select_option('cyan')
        check(preset + '_advanced_disclosure_retained', page.locator('form details').get_attribute('open') is not None and page.locator('#f-source-scrape_bare_ids').is_checked())
    b.close()
report['prototype_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in ['workflow-engine.js', 'workflow-data.js', 'workflow-prototype.html', 'workflow-prototype.css', 'presentation-presets.css']}
report['summary'] = {'passed': sum(report['checks'].values()), 'failed': sum(not v for v in report['checks'].values()), 'errors': len(report['errors']), 'blocked': len(report['blocked'])}
(out / 'journey-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report['summary'], indent=2))
raise SystemExit(bool(report['summary']['failed'] or report['errors'] or report['blocked']))
