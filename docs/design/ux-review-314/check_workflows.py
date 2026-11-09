"""Isolated review-06 design checks. No application, supplier or installation execution.

Uses existing cached Playwright/Chromium and optional axe. All browser requests are
fulfilled from this public design directory at design.invalid; everything else aborts.
Reports belong outside git. --exports writes deliberately synthetic gallery images.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote, urlencode
import argparse, itertools, json, mimetypes, time
from playwright.sync_api import sync_playwright

ap=argparse.ArgumentParser()
ap.add_argument('--output',required=True)
ap.add_argument('--axe')
ap.add_argument('--presets',default='lime,coral,cyan')
ap.add_argument('--smoke',action='store_true')
ap.add_argument('--interactions-only',action='store_true')
ap.add_argument('--exports',action='store_true')
ap.add_argument('--only',help='Comma-separated workflows for focused iteration')
args=ap.parse_args()
ROOT=Path(__file__).resolve().parent
OUT=Path(args.output).resolve();OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((ROOT/'workflow-data.json').read_text())
screens=[s for s in data['screens'] if not args.only or s['id'] in args.only.split(',')]
report=dict(revision=data['revision'],screens=len(screens),layouts=[],a11y=[],functional={},console=[],errors=[],blocked=[],exports=[],reflow=[])
start=time.monotonic()
CHECK_LAYOUT="""() => {
 const visible=e=>e.getClientRects().length && getComputedStyle(e).visibility!=='hidden';
 const bad=[];
 for(const e of document.querySelectorAll('main button,main a,main label,main input,main select,main textarea,main summary,.study-tools select')){
  if(!visible(e))continue;
  const r=e.getBoundingClientRect();
  if(r.left < -1 || r.right > innerWidth+1)bad.push({tag:e.tagName,id:e.id,text:(e.innerText||e.getAttribute('aria-label')||'').slice(0,80),left:r.left,right:r.right});
  if(['BUTTON','SUMMARY'].includes(e.tagName)&&e.scrollWidth>e.clientWidth+2)bad.push({id:e.id,text:e.innerText,clip:'control content'});
 }
 return {overflow:document.documentElement.scrollWidth>innerWidth+1,clipped:bad,multipleCurrentTabs:document.querySelectorAll('.section-nav [aria-current]').length>1,main:document.querySelectorAll('main').length,h1:document.querySelectorAll('h1').length,language:document.documentElement.lang};
}"""
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True)
 context=browser.new_context(service_workers='block',reduced_motion='reduce',accept_downloads=False)
 if args.axe:context.add_init_script(path=str(Path(args.axe).resolve()))
 def intercept(route):
  u=urlsplit(route.request.url);path=(ROOT/unquote(u.path).lstrip('/')).resolve()
  if u.hostname!='design.invalid' or route.request.method!='GET' or not path.is_relative_to(ROOT) or not path.is_file():
   report['blocked'].append(dict(method=route.request.method,url=u.path));route.abort();return
  route.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
 context.route('**/*',intercept)
 page=context.new_page()
 page.on('pageerror',lambda error:report['errors'].append(str(error)))
 page.on('console',lambda m:report['console'].append(dict(type=m.type,text=m.text)) if m.type in ['warning','error'] else None)
 def go(screen,lang='en',theme='light',width=1440,**extra):
  page.set_viewport_size(dict(width=width,height=900))
  page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen=screen,lang=lang,theme=theme,review=1,**extra)),wait_until='load')
  page.evaluate('document.fonts.ready')
  page.wait_for_selector('main h1')
 def layout(label):
  r=page.evaluate(CHECK_LAYOUT);r['case']=label;report['layouts'].append(r)
 def axe(label):
  if not args.axe:return
  r=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.length}))}}")
  report['a11y'].append(dict(case=label,**r))
 for i,s in enumerate([] if args.interactions_only else screens):
  sid=s['id']
  presets=args.presets.split(',')
  combinations=[('en','light',1440),('es','dark',390)] if args.smoke else list(itertools.product(['en','es'],['light','dark'],[320,820,1440]))
  for preset in presets:
   for lang,theme,width in combinations:
    go(sid,lang,theme,width,preset=preset);layout(f'{sid}/{preset}/{lang}/{theme}/{width}')
   for lang,theme,width in [('en','light',1440),('es','dark',390)]:
    go(sid,lang,theme,width,preset=preset)
    page.evaluate("document.querySelectorAll('form details').forEach(d=>d.open=true)")
    layout(f'{sid}/{preset}/{lang}/{theme}/{width}/advanced');axe(f'{sid}/{preset}/{lang}/{theme}/{width}')
    if args.exports:
     page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen=sid,lang=lang,theme=theme,preset=preset,presentation=1)),wait_until='load')
     page.evaluate('document.fonts.ready')
     page.evaluate('async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))}')
     dest=ROOT/'workflow-exports'/f'{sid}-{preset}-{lang}.jpg';dest.parent.mkdir(exist_ok=True)
     page.screenshot(path=str(dest),full_page=True,type='jpeg',quality=65)
     report['exports'].append(str(dest.relative_to(ROOT)))
   if not args.smoke:
    for st in list(dict.fromkeys(s['baseStates']+list(s.get('states',{})))):
     stateaxes=[('en','light'),('es','dark')] if st in s.get('states',{}) else [('es','dark')]
     for lang,theme in stateaxes:
      go(sid,lang,theme,390,preset=preset,state=st);layout(f'{sid}/{preset}/{lang}/{theme}/390/{st}')
  if i%10==0:print(f'Workflow {i+1}/{len(screens)}; layouts {len(report["layouts"])}; axe {len(report["a11y"])}',flush=True)
 (OUT/'workflow-layout-stage.json').write_text(json.dumps(report,indent=2))
 # Focused interactions across materially different contracts.
 checks=report['functional']
 def check(name,condition):checks[name]=bool(condition)
 if not args.only:
  go('unsaved');page.locator('#f-draft-source_name').fill('Edited synthetic source')
  page.locator('#lang-select').focus();page.locator('#lang-select').select_option('es')
  check('locale_keeps_draft',page.locator('#f-draft-source_name').input_value()=='Edited synthetic source')
  check('locale_keeps_focus',page.locator(':focus').get_attribute('id')=='lang-select')
  page.locator('#theme-select').select_option('dark');check('theme_keeps_draft',page.locator('#f-draft-source_name').input_value()=='Edited synthetic source')
  page.locator('#screen-select').focus();page.locator('#screen-select').select_option('dashboard');check('dirty_guard',page.locator('#confirm').is_visible())
  check('safe_cancel_focus',page.locator(':focus').get_attribute('id')=='confirm-cancel')
  page.keyboard.press('Shift+Tab');check('modal_focus_trap',page.locator(':focus').get_attribute('id')=='confirm-commit')
  page.keyboard.press('Escape');check('escape_cancel',not page.locator('#confirm').is_visible())
  check('focus_returns',page.locator(':focus').get_attribute('id')=='screen-select')
  check('escape_keeps_draft',page.locator('#f-draft-source_name').input_value()=='Edited synthetic source')
  page.locator('#screen-select').focus();page.locator('#screen-select').select_option('dashboard');page.locator('#confirm-commit').click();check('discard_navigates',page.evaluate('__workflow.current')=='dashboard')
  go('recording-settings');check('pristine_save_disabled',page.locator('#form-recording-settings [type=submit]').is_disabled())
  page.locator('#f-recordings-max_concurrent').fill('5');check('range_error',page.locator('#f-recordings-max_concurrent').get_attribute('aria-invalid')=='true')
  check('invalid_save_disabled',page.locator('#form-recording-settings [type=submit]').is_disabled())
  page.locator('#f-recordings-max_concurrent').fill('2');check('valid_dirty_save',page.locator('#form-recording-settings [type=submit]').is_enabled())
  page.locator('#f-recordings-retention_enabled').check();check('dependent_retention',page.locator('#f-recordings-retention_days').is_enabled())
  page.locator('#form-recording-settings [data-action=reset]').click();check('cancel_restores_limits',page.locator('#f-recordings-max_concurrent').input_value()=='1')
  go('recording-dst');page.locator('#f-recording-start_choice').select_option('2026-10-25T01:30:00Z');page.locator('#f-recording-end_choice').select_option('2026-10-25T00:50:00Z')
  check('dst_compares_instants',page.locator('#form-dst [type=submit]').is_disabled())
  page.locator('#f-recording-end_choice').select_option('2026-10-25T01:50:00Z');check('dst_valid_instants',page.locator('#form-dst [type=submit]').is_enabled())
  go('guide-match');check('guide_no_preselection',page.locator('[data-action=apply-choice]').is_disabled())
  page.locator('[data-choice]').first.check();page.locator('#lang-select').focus();page.locator('#lang-select').select_option('es');check('locale_keeps_review_selection',page.locator('[data-choice]').first.is_checked())
  page.locator('#state-select').select_option('conflict');check('stale_clears_selection',not page.locator('[data-choice]').first.is_checked())
  check('stale_blocks_apply',page.locator('[data-action=apply-choice]').is_disabled())
  go('guide-export');names=page.get_by_role('slider').evaluate_all('(els)=>els.map(e=>document.querySelector(`label[for="${e.id}"]`).textContent)')
  check('range_controls_have_distinct_names',len(set(names))==2)
  page.locator('#f-xml-days_forward').focus();page.keyboard.press('Home');check('guide_range_order',page.locator('#form-xml [type=submit]').is_disabled())
  go('channel-reorder');before=page.locator('.order-row strong').all_text_contents();page.locator('[data-action=down]').first.click()
  check('arrow_reorders_complete_list',page.locator('.order-row strong').all_text_contents()==[before[1],before[0],before[2]])
  page.locator('[data-action=reset-order]').click();check('cancel_order_restores',page.locator('.order-row strong').all_text_contents()==before)
  page.locator('[data-action=drag]').first.focus();page.keyboard.press('Alt+ArrowDown');check('keyboard_reorders',page.locator('.order-row strong').all_text_contents()[1]==before[0])
  go('playlist');page.locator('#f-playlist-favorites_only').check();check('favorites_disables_unassigned',page.locator('#f-playlist-include_unassigned').is_disabled())
  go('access-account');page.locator('#f-account-administrator').check();check('admin_disables_misleading_permissions',page.locator('#f-permissions-live').is_disabled())
  go('access-password');page.locator('#f-account-password').fill('synthetic-password');page.locator('#f-password-password_confirmation').fill('different');check('password_confirmation',page.locator('#form-password [type=submit]').is_disabled())
  go('live');page.evaluate('window.playerIdentity=document.getElementById("synthetic-player")');page.locator('#f-live-q').fill('no match');page.locator('#lang-select').focus();page.locator('#lang-select').select_option('es')
  check('live_player_node_retained',page.evaluate('playerIdentity===document.getElementById("synthetic-player")'))
  check('view_filter_not_unsaved_settings',not page.evaluate('__workflow.dirty'))
  check('live_filtered_empty_is_visible',page.locator('#local-filter-empty').is_visible() and page.locator('.workflow-rows li:visible').count()==0)
  check('original_programme_name_retained','Coastlines: the Atlantic' in page.locator('main').inner_text())
  go('helper-results',context='standalone');check('standalone_no_installed_apply',page.locator('[data-action=command]').count()==0)
  go('helper-standalone',width=390);check('direct_standalone_has_no_installation_navigation',page.locator('.study-layout>.sidebar').count()==0 and page.locator('#menu-open').count()==0)
  page.locator('#f-sample-file').set_input_files({'name':'synthetic-sample.txt','mimeType':'text/plain','buffer':b'Northlight synthetic fixture'});page.locator('#lang-select').focus();page.locator('#lang-select').select_option('es');check('file_picker_localized_and_retained',page.locator('[data-action=choose-file]').inner_text()=='Elegir archivo local' and page.locator('#f-sample-file').evaluate('(e)=>e.files[0].name')=='synthetic-sample.txt')
  go('stream-bulk');check('bulk_delete_needs_selection',page.locator('[data-action=command]').is_disabled());page.locator('[data-choice]').first.check();check('bulk_delete_enabled_after_selection',page.locator('[data-action=command]').is_enabled())
  go('stream-match');check('similar_suggestions_off_initially',page.locator('[data-requires]').is_hidden());page.locator('#f-matching-include_similar').check();check('similar_suggestions_explicit_opt_in',page.locator('[data-requires]').is_visible());page.locator('[data-requires] input').check();page.locator('#f-matching-include_similar').uncheck();check('changing_match_scope_clears_selection',page.locator('[data-action=apply-choice]').is_disabled())
  go('casting-control');check('cast_volume_uses_percent',page.locator('#f-cast-volume').get_attribute('aria-valuetext')=='50 percent')
  go('access-password');page.locator('#f-password-current_password').fill('DEMO current password');page.locator('#f-account-password').fill('🟩'*128);page.locator('#f-password-password_confirmation').fill('🟩'*128);check('password_limits_count_unicode_characters',page.locator('#form-password [type=submit]').is_enabled())
  go('access-account',state='last-admin');check('last_admin_state_blocks_submit',page.locator('#form-account [type=submit]').is_disabled())
  go('event-import');page.locator('#f-event-input').select_option('json');check('json_mode_does_not_require_manual_title',page.locator('#f-event-title').is_disabled());page.locator('form details').first.evaluate('(e)=>e.open=true');check('json_mode_exposes_json_field',page.locator('#f-event-json').is_enabled())
  go('warp');check('warp_separate_transactions',page.locator('form').count()==2)
  go('automation');check('schedule_separate_transactions',page.locator('form').count()==5)
  page.locator('#f-schedule-rescrape_interval').fill('25');page.locator('#f-schedule-epg_refresh_interval').fill('8')
  page.locator('#form-intervals-0 [type=submit]').click()
  check('pending_blocks_duplicate_submission',page.locator('#form-intervals-0 [type=submit]').is_disabled())
  check('pending_keeps_other_transaction_available',page.locator('#form-intervals-1 [type=submit]').is_enabled())
  page.wait_for_function("()=>document.querySelector('#form-intervals-0 .workflow-status').textContent.includes('Only this setting')")
  check('saving_one_keeps_other_dirty',page.evaluate('__workflow.dirty') and page.locator('#form-intervals-1 [type=submit]').is_enabled())
  go('channel-inline');page.locator('#f-inline-number').fill('27');page.keyboard.press('Escape');check('number_escape_restores',page.locator('#f-inline-number').input_value()=='12')
  page.locator('#f-inline-number').fill('');page.keyboard.press('Enter');page.wait_for_function("()=>document.querySelector('#form-inline-number .workflow-status').textContent.includes('Number saved')")
  check('number_blank_saves_clear',page.locator('#f-inline-number').input_value()=='' and not page.evaluate('__workflow.dirty'))
  page.locator('#f-inline-favorite').check();page.wait_for_function("()=>document.querySelector('#form-inline-favorite .workflow-status').textContent.includes('Favorite saved')")
  check('favorite_immediate_save',not page.evaluate('__workflow.dirty'))
  go('recording-schedule');page.locator('#f-recording-adjust_times').check();page.locator('#f-recording-start_time').fill('2026-03-29T02:30');check('missing_dst_time_invalid',page.locator('#f-recording-start_time').get_attribute('aria-invalid')=='true')
  go('w3u-save');check('w3u_save_without_import',page.locator('#form-catalogue-save [type=submit]').is_enabled())
  go('settings',width=390);page.locator('#menu-open').click();check('phone_drawer_modal',page.locator('#drawer').evaluate('(e)=>e.matches(":modal")'))
  page.keyboard.press('Escape');check('phone_drawer_focus_returns',page.locator(':focus').get_attribute('id')=='menu-open')
  go('recording-delete');page.locator('[data-action=command]').click();check('destructive_names_consequence','Coastlines' in page.locator('#confirm-body').inner_text())
  check('destructive_safe_initial_focus',page.locator(':focus').get_attribute('id')=='confirm-cancel');axe('delete-confirm-dialog');page.keyboard.press('Escape')
  # Deliberately labelled text enlargement and 320 CSS-pixel reflow; not an OS zoom claim.
  for sid in ['access-activate','recording-schedule','channels','guide-export','helper-html','runtime-network','recovery-fresh']:
   go(sid,'es','dark',320);page.evaluate("document.querySelectorAll('form details').forEach(d=>d.open=true)")
   r=page.evaluate(CHECK_LAYOUT);report['reflow'].append(dict(case=sid+'/320-css-pixel-reflow',**r))
   go(sid,'es','light',1280);page.add_style_tag(content='p,label,input,select,textarea,button,summary,dt,dd,a,small{font-size:200%!important}')
   r=page.evaluate(CHECK_LAYOUT);report['reflow'].append(dict(case=sid+'/200-percent-text-stress',**r))
  go('dashboard',state='first-use');check('first_use_has_no_populated_hero',page.locator('.watch-hero').count()==0 and 'Add a channel source' in page.locator('main').inner_text())
  go('stream-stats',state='unknown');check('unknown_statistics_not_zero', 'Unknown · not zero' in page.locator('main').inner_text())
  go('event-detail',state='unknown');check('date_only_has_no_invented_time', 'World Friendly' in page.locator('main').inner_text() and '00:00' not in page.locator('main').inner_text())
  go('access-activate',state='blocked');check('public_http_blocks_password_entry',page.locator('input[type=password]').count()==0)
  go('recording-active',state='finalizing');check('finalizing_locks_stop_and_edit',page.locator('[data-action=command]').is_disabled() and page.locator('[data-field="recording.end_time"]').is_disabled())
  check('reduced_motion',page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches'))
  check('only_design_preference_storage',page.evaluate("Object.keys(localStorage).every(k=>k==='ace-design-314:preset') && sessionStorage.length===0"))
  check('no_real_media_elements',page.locator('video,audio,iframe').count()==0)
  # Same behavioral contract across presentation presets.
  for preset in ['lime','coral','cyan']:
   go('unsaved',preset=preset,channel='fixture-channel',returnTo='recordings')
   page.locator('#f-draft-source_name').fill('Kept draft')
   page.locator('#preset-select').focus();page.locator('#preset-select').select_option('cyan' if preset!='cyan' else 'lime')
   check(preset+'_preset_keeps_draft',page.locator('#f-draft-source_name').input_value()=='Kept draft')
   check(preset+'_preset_keeps_focus',page.locator(':focus').get_attribute('id')=='preset-select')
   check(preset+'_preset_keeps_query','channel=fixture-channel' in page.url and 'returnTo=recordings' in page.url)
   go('guide-match',preset=preset);page.locator('[data-choice]').first.check();page.locator('#preset-select').select_option('coral' if preset!='coral' else 'lime')
   check(preset+'_preset_keeps_selection',page.locator('[data-choice]').first.is_checked())
   go('live',preset=preset);page.evaluate('window.retainedPlayer=document.getElementById("synthetic-player")');owner=page.evaluate('__workflow.playback.owner');page.locator('#preset-select').select_option('coral')
   check(preset+'_preset_keeps_player',page.evaluate('retainedPlayer===document.getElementById("synthetic-player")') and page.evaluate('__workflow.playback.owner')==owner)
   go('automation',preset=preset);page.clock.install();page.clock.pause_at(page.evaluate('Date.now()')+1000)
   page.locator('#f-schedule-rescrape_interval').fill('25');page.locator('#form-intervals-0 [type=submit]').click();page.locator('#preset-select').select_option('cyan')
   check(preset+'_preset_keeps_pending',page.evaluate('__workflow.pending')==1 and page.locator('#form-intervals-0 [type=submit]').is_disabled())
   page.clock.fast_forward(250);check(preset+'_pending_finishes_after_switch',page.evaluate('__workflow.pending')==0 and not page.evaluate('__workflow.dirty'))
   page.clock.resume()
  go('dashboard',preset='not-known');check('unknown_preset_falls_back_cyan',page.evaluate('__workflow.preset')=='cyan')
  page.locator('#appearance-open').click();check('preset_dialog_modal',page.locator('#appearance').evaluate('(e)=>e.matches(":modal")'))
  page.locator('#appearance [data-preset=coral]').click();check('preset_choice_applies',page.evaluate('__workflow.preset')=='coral')
  page.locator('#appearance-close').click();check('preset_dialog_focus_returns',page.locator(':focus').get_attribute('id')=='appearance-open')
  page.goto('http://design.invalid/workflow-prototype.html?screen=dashboard&review=1');check('preset_remembered',page.evaluate('__workflow.preset')=='coral')
  go('preferences',preset='cyan',storage='failed');page.locator('#workflow-content [data-preset=lime]').click();check('storage_failure_keeps_choice',page.evaluate('__workflow.preset')=='lime' and page.locator('[data-action=retry-storage]').is_visible())
  go('dashboard');check('online_only_default',not page.locator('#watch-all').is_checked() and page.locator('[data-watch-card]:visible').count()==2)
  page.locator('#watch-all').check();check('show_all_adds_unverified',page.locator('[data-watch-card]:visible').count()==3)
  page.locator('#watch-search').fill('Atelier');check('watch_filter_works',page.locator('[data-watch-card]:visible').count()==1)
  page.locator('[data-watch-card]:visible [data-action=watch]').click();check('watch_starts_selected_fixture',page.evaluate('__workflow.playback.active') and page.evaluate('__workflow.playback.channel')=='Atelier')
  go('guide-auto');page.locator('#f-epg_matching-enabled').check();page.wait_for_function('()=>__workflow.pending===0');check('guide_auto_immediate_no_confirm',not page.locator('#confirm').is_visible() and not page.evaluate('__workflow.dirty'))
  go('event-detail');check('event_artwork_explicit_initially',page.locator('.event-artwork img').count()==0);page.locator('[data-action=load-artwork]').click();check('event_artwork_explicit_load',page.locator('.event-artwork img').count()==1)
  go('setup-source');check('setup_reuses_source_editor',page.evaluate('__workflow.current')=='source-web')
  go('setup-guide');check('setup_reuses_guide_editor',page.evaluate('__workflow.current')=='guide-source')
 browser.close()
failures=[x for x in report['layouts']+report['reflow'] if x.get('multipleCurrentTabs') or x['overflow'] or x['clipped'] or x['main']!=1 or x['h1']!=1]
report['elapsed_seconds']=round(time.monotonic()-start,1)
report['summary']=dict(screens=len(screens),layout_cases=len(report['layouts']),layout_failures=len(failures),axe_cases=len(report['a11y']),axe_violating_cases=sum(bool(x['violations']) for x in report['a11y']),functional_pass=sum(report['functional'].values()),functional_fail=sum(not x for x in report['functional'].values()),reflow_cases=len(report['reflow']),errors=len(report['errors']),console=len(report['console']),blocked=len(report['blocked']),exports=len(report['exports']))
report['failures']=failures
(OUT/'workflow-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report['summary'],indent=2),flush=True)
failed=bool(failures or any(x['violations'] for x in report['a11y']) or any(not x for x in report['functional'].values()) or report['errors'] or report['console'] or report['blocked'])
raise SystemExit(1 if failed else 0)
