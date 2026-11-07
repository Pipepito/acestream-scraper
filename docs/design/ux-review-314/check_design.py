"""Isolated design checks; never contacts an application installation.
Usage: python3 docs/design/ux-review-314/check_design.py --output /tmp/ux-design-checks
Requires existing Python Playwright, a cached Chromium and optional --axe path.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright
import argparse, itertools, json, mimetypes, re, subprocess, sys

ap=argparse.ArgumentParser()
ap.add_argument('--output',required=True)
ap.add_argument('--axe')
ap.add_argument('--screenshots',action='store_true')
ap.add_argument('--workflows-only',action='store_true',help='Run the expanded review-04 workflow matrix instead of the historical prototypes')
args=ap.parse_args()
ROOT=Path(__file__).resolve().parent
if args.workflows_only:
 command=[sys.executable,str(ROOT/'check_workflows.py'),'--output',args.output]
 if args.axe:command+=['--axe',args.axe]
 if args.screenshots:command+=['--exports']
 raise SystemExit(subprocess.run(command).returncode)
OUT=Path(args.output).resolve();OUT.mkdir(parents=True,exist_ok=True)
results=[];errors=[];console=[];blocked=[];a11y=[];checks={}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  self.refs.extend(v for k,v in attrs if k in ('href','src') and v)
refs=[]
for f in ROOT.iterdir():
 if f.suffix=='.md':refs.extend((f,m) for m in re.findall(r'\]\(([^ )]+)',f.read_text()))
 if f.suffix=='.html':
  parser=Links();parser.feed(f.read_text());refs.extend((f,r) for r in parser.refs)
 if f.suffix=='.css':refs.extend((f,m) for m in re.findall(r'url\([\'"]?([^\'")]+)',f.read_text()))
local=[(f,unquote(urlsplit(r).path)) for f,r in refs if not urlsplit(r).scheme and urlsplit(r).path and not r.startswith('{')]
missing=[str(f.name)+': '+r for f,r in local if not (f.parent/r).exists()]
checks['local_links']={'count':len(local),'missing':missing}

with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 ctx=b.new_context(service_workers='block',reduced_motion='reduce',accept_downloads=False)
 def route(r):
  u=urlsplit(r.request.url);path=(ROOT/unquote(u.path).lstrip('/')).resolve()
  if u.hostname!='design.invalid' or r.request.method!='GET' or not path.is_relative_to(ROOT) or not path.is_file():
   blocked.append({'method':r.request.method,'path':u.path});r.abort();return
  r.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
 ctx.route('**/*',route);page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('console',lambda m:console.append({'type':m.type,'text':m.text}) if m.type in ('warning','error') else None)
 def go(query):
  page.goto('http://design.invalid/admin-prototype.html?'+query,wait_until='load')
  page.evaluate('document.fonts.ready')
 def record(label):
  results.append({'case':label,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth'),'main':page.locator('main').count(),'h1':page.locator('h1').count()})
 views=['recordings','guide','access','sources','connections','system','setup','recovery','helper']
 for v,lang,theme,palette,direction,width in itertools.product(views,['en','es'],['light','dark'],['coral','lime'],['calm','broadcast'],[320,390,768,1440]):
  page.set_viewport_size({'width':width,'height':900})
  query=f'view={v}&lang={lang}&theme={theme}&palette={palette}&direction={direction}'
  go(query);record(query+f'&width={width}')
 print('Populated layout cases:',len(results),flush=True)
 # All meaningful states, both languages/themes and phone/desktop.
 for v in views:
  go('view='+v);states=page.evaluate('applicable[view].filter(s=>s!=="ready")')
  for s,lang,theme,width in itertools.product(states,['en','es'],['light','dark'],[390,1440]):
   page.set_viewport_size({'width':width,'height':900})
   query=f'view={v}&state={s}&lang={lang}&theme={theme}'
   go(query);record(query+f'&width={width}')
 print('All new layout/state cases:',len(results),flush=True)
 # Automated accessibility triage; no claim of full conformance.
 if args.axe:
  for v,lang,theme,width in itertools.product(views,['en','es'],['light','dark'],[390,1440]):
   page.set_viewport_size({'width':width,'height':900});go(f'view={v}&lang={lang}&theme={theme}')
   page.add_script_tag(path=str(Path(args.axe).resolve()))
   findings=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}")
   a11y.append({'view':v,'lang':lang,'theme':theme,'width':width,'violations':findings})
  print('Accessibility scans:',len(a11y),flush=True)
 page.set_viewport_size({'width':1440,'height':1000})
 go('view=sources')
 page.locator('#source').fill('Edited sample')
 page.locator('#lang').click();checks['locale_changes_document']=page.locator('html').get_attribute('lang')=='es';checks['locale_keeps_draft']=page.locator('#source').input_value()=='Edited sample'
 page.locator('#theme').click();checks['theme_changes']=page.locator('body').evaluate('(e)=>e.classList.contains("dark")');checks['theme_keeps_draft']=page.locator('#source').input_value()=='Edited sample'
 page.locator('#view-select').select_option('system')
 checks['dirty_guard']=page.locator('dialog').is_visible()
 page.locator('#dialog-cancel').click()
 checks['cancel_navigation_keeps_draft']=page.locator('#source').input_value()=='Edited sample'
 page.locator('#view-select').select_option('system');page.locator('#dialog-commit').click()
 checks['discard_navigation']=page.locator('h1').inner_text()=='Estado del sistema'
 go('view=guide')
 page.locator('.match input').first.check();page.locator('#lang').click()
 checks['locale_keeps_selection']=page.locator('.match input').first.is_checked()
 checks['original_names_preserved']='Northlight' in page.locator('main').inner_text()
 page.locator('#state-select').select_option('conflict')
 checks['conflict_clears_selection']=not page.locator('.match input').first.is_checked()
 go('view=recordings&state=destructive')
 checks['safe_initial_focus']=page.locator(':focus').get_attribute('id')=='dialog-cancel'
 page.keyboard.press('Escape');checks['escape_closes_dialog']=not page.locator('dialog').is_visible()
 go('view=access');checks['pristine_save_disabled']=page.get_by_role('button',name='Save changes',exact=True).is_disabled()
 page.locator('.check input').first.uncheck();checks['dirty_save_enabled']=page.get_by_role('button',name='Save changes',exact=True).is_enabled()
 # Historical prototype: verify previous layout baseline separately.
 old=[]
 for v,lang,theme,palette,width in itertools.product(['live','settings','channels'],['en','es'],['light','dark'],['lime','coral'],[320,390,768,1440]):
  page.set_viewport_size({'width':width,'height':900})
  page.goto(f'http://design.invalid/prototype.html?view={v}&lang={lang}&theme={theme}&palette={palette}',wait_until='load')
  old.append({'view':v,'lang':lang,'theme':theme,'palette':palette,'width':width,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')})
 checks['historical_layouts']={'count':len(old),'failures':[x for x in old if x['overflow']]}
 if args.screenshots:
  for i,v in enumerate(views,14):
   for lang,theme,width,height in [('en','light',1440,1000),('es','dark',390,844)]:
    page.set_viewport_size({'width':width,'height':height});go(f'view={v}&lang={lang}&theme={theme}&presentation=1')
    page.screenshot(path=str(OUT/f'{i}-{v}-{lang}.png'),full_page=True)
  for v,s in [('guide','conflict'),('sources','error'),('access','destructive'),('recovery','destructive')]:
   page.set_viewport_size({'width':1200,'height':1000});go(f'view={v}&state={s}&lang=es&theme=dark&presentation=1')
   page.screenshot(path=str(OUT/f'state-{v}-{s}.png'),full_page=True)
  for direction,palette in [('calm','coral'),('calm','lime'),('broadcast','coral'),('broadcast','lime')]:
   page.set_viewport_size({'width':1440,'height':1000});go(f'view=recordings&direction={direction}&palette={palette}&theme=dark&presentation=1')
   page.screenshot(path=str(OUT/f'compare-{direction}-{palette}.png'),full_page=True)
 gallery=[]
 for width in [320,390,768,1440]:
  page.set_viewport_size({'width':width,'height':900});page.goto('http://design.invalid/index.html',wait_until='load')
  page.evaluate('document.querySelectorAll("img").forEach(i=>i.loading="eager")')
  page.wait_for_function('[...document.images].every(i=>i.complete)',timeout=15000)
  decoded=page.evaluate('async()=>{const imgs=[...document.images];await Promise.all(imgs.map(i=>i.decode().catch(()=>null)));return imgs.filter(i=>!i.naturalWidth).length}')
  gallery.append({'width':width,'images':page.locator('img').count(),'brokenImages':decoded,'overflow':page.evaluate('document.documentElement.scrollWidth>innerWidth')})
 checks['gallery']=gallery
 b.close()
data={'layout_cases':len(results),'layout_failures':[r for r in results if r['overflow'] or r['main']!=1 or r['h1']!=1],'script_errors':errors,'console':console,'blocked_requests':blocked,'checks':checks,'a11y':a11y}
(OUT/'checks.json').write_text(json.dumps(data,indent=2))
fail=bool(data['layout_failures'] or errors or console or blocked or missing or checks['historical_layouts']['failures'] or any(x is False for x in checks.values()) or any(x['violations'] for x in a11y) or any(g['brokenImages'] or g['overflow'] or g['images']!=39 for g in gallery))
print(json.dumps({'cases':len(results),'layoutFailures':len(data['layout_failures']),'errors':errors,'links':checks['local_links'],'a11yCasesWithViolations':sum(bool(x['violations']) for x in a11y),'functional':{k:v for k,v in checks.items() if isinstance(v,bool)},'gallery':gallery,'historical':checks['historical_layouts'],'failed':fail},indent=2))
raise SystemExit(1 if fail else 0)
