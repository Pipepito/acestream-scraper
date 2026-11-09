"""Isolated gallery, critical-state accessibility and computed-token contrast checks."""
from pathlib import Path
from urllib.parse import urlsplit, unquote, urlencode
from playwright.sync_api import sync_playwright
import argparse,json,mimetypes,re

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--axe',required=True);args=ap.parse_args()
ROOT=Path(__file__).resolve().parent;OUT=Path(args.output);OUT.mkdir(parents=True,exist_ok=True)
report=dict(gallery=[],states=[],contrast=[],errors=[],console=[],blocked=[])
critical=[('event-detail','unknown'),('dashboard','first-use'),('stream-stats','unknown'),('recording-dst','gap'),('recording-active','starting'),('recording-active','interrupted'),('recording-settings','unavailable'),('access-activate','blocked'),('access-account','last-admin'),('channel-reorder','conflict'),('guide-match','conflict'),('source-results','partial'),('w3u','expired'),('helper-large','too-large'),('live','refreshing'),('live','failed'),('event-overlay','conflict'),('remote-android','expired'),('telegram-auth','flood'),('warp-exclusions','partial'),('offline-cleanup','refresh-failed'),('storage','partial'),('recovery','busy')]
def rgb(value):
 value=value.strip()
 if value.startswith('#'):return [int(value[i:i+2],16)/255 for i in (1,3,5)]
 return [float(x)/255 for x in re.findall(r'[\d.]+',value)[:3]]
def lum(color):
 vals=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb(color)]
 return sum(v*w for v,w in zip(vals,[.2126,.7152,.0722]))
def ratio(a,b):
 lo,hi=sorted([lum(a),lum(b)]);return (hi+.05)/(lo+.05)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True);report['browser']=browser.version
 ctx=browser.new_context(service_workers='block',reduced_motion='reduce');ctx.add_init_script(path=str(Path(args.axe).resolve()))
 def route(r):
  u=urlsplit(r.request.url);path=(ROOT/unquote(u.path).lstrip('/')).resolve()
  if u.hostname!='design.invalid' or r.request.method!='GET' or not path.is_relative_to(ROOT) or not path.is_file():report['blocked'].append(u.path);r.abort();return
  r.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
 ctx.route('**/*',route);page=ctx.new_page()
 page.on('pageerror',lambda e:report['errors'].append(str(e)))
 page.on('console',lambda m:report['console'].append(m.text) if m.type in ['warning','error'] else None)
 for width in [320,390,768,1440]:
  page.set_viewport_size(dict(width=width,height=900));page.goto('http://design.invalid/workflow-gallery.html')
  result=page.evaluate("async()=>{document.querySelectorAll('img').forEach(i=>i.loading='eager');await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)));return {images:document.images.length,broken:[...document.images].filter(i=>!i.naturalWidth).length,overflow:document.documentElement.scrollWidth>innerWidth+1}}")
  report['gallery'].append(dict(width=width,**result))
 for sid,state in critical:
  for lang,theme,width,preset in [(l,t,w,p) for l,t,w in [('en','light',1440),('es','dark',390)] for p in ['lime','coral','cyan']]:
   page.set_viewport_size(dict(width=width,height=900));page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen=sid,state=state,lang=lang,theme=theme,preset=preset)));page.evaluate('document.fonts.ready')
   r=page.evaluate("async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}}")
   report['states'].append(dict(screen=sid,state=state,lang=lang,theme=theme,preset=preset,**r))
 for theme in ['light','dark']:
  for palette in ['coral','lime','cyan']:
   page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen='casting-control',theme=theme,preset=palette)));page.evaluate('document.fonts.ready')
   tokens=page.evaluate("()=>Object.fromEntries(['bg','surface','subtle','text','muted','accent','ink','selected','selected-text','good','good-bg','warn','warn-bg','bad','bad-bg','focus','control'].map(k=>[k,getComputedStyle(document.body).getPropertyValue('--'+k).trim()]))")
   for a,b,required in [('text','bg',4.5),('text','surface',4.5),('muted','bg',4.5),('muted','surface',4.5),('muted','subtle',4.5),('ink','accent',4.5),('selected-text','selected',4.5),('good','good-bg',4.5),('warn','warn-bg',4.5),('bad','bad-bg',4.5),('focus','bg',3),('focus','surface',3),('control','surface',3)]:
    measured=ratio(tokens[a],tokens[b]);report['contrast'].append(dict(theme=theme,preset=palette,pair=a+'/'+b,ratio=round(measured,3),required=required,passed=measured>=required))
 report['axe_version']=page.evaluate('axe.version')
 browser.close()
bad_gallery=[x for x in report['gallery'] if x['images']!=146 or x['broken'] or x['overflow']]
report['summary']=dict(gallery_widths=len(report['gallery']),gallery_images=146,gallery_failures=len(bad_gallery),critical_state_axe_cases=len(report['states']),axe_violating_cases=sum(bool(x['violations']) for x in report['states']),contrast_pairs=len(report['contrast']),contrast_failures=sum(not x['passed'] for x in report['contrast']),minimum_text_ratio=min(x['ratio'] for x in report['contrast'] if x['required']==4.5),minimum_ui_ratio=min(x['ratio'] for x in report['contrast'] if x['required']==3),errors=len(report['errors']),console=len(report['console']),blocked=len(report['blocked']))
(OUT/'gallery-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['summary'],indent=2))
raise SystemExit(bool(bad_gallery or any(x['violations'] for x in report['states']) or any(not x['passed'] for x in report['contrast']) or report['errors'] or report['console'] or report['blocked']))
