"""Static preview packaging and representative long-content checks."""
from pathlib import Path
from urllib.parse import urlsplit,unquote,urlencode
import argparse,json,mimetypes
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parent));ap.add_argument('--output',required=True);ap.add_argument('--axe',required=True);a=ap.parse_args();root=Path(a.root).resolve();out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
r={'pages':[],'contrast_review':[],'long_content':[],'errors':[],'blocked':[],'console':[]}
with sync_playwright() as p:
 b=p.chromium.launch();c=b.new_context(service_workers='block',reduced_motion='reduce');c.add_init_script(path=a.axe)
 def intercept(route):
  u=urlsplit(route.request.url);f=(root/unquote(u.path).lstrip('/')).resolve()
  if u.hostname!='design.invalid' or route.request.method!='GET' or not f.is_relative_to(root) or not f.is_file():r['blocked'].append(u.path);route.abort();return
  route.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(f.name)[0] or 'text/plain')
 c.route('**/*',intercept);page=c.new_page();page.on('pageerror',lambda e:r['errors'].append(str(e)));page.on('console',lambda m:r['console'].append(m.text) if m.type in ['warning','error'] else None)
 for file in ['index.html','workflow-gallery.html']:
  for width in [320,390,820,1440]:
   page.set_viewport_size({'width':width,'height':900});page.goto('http://design.invalid/'+file);page.evaluate('document.fonts.ready')
   result=page.evaluate("async()=>{document.querySelectorAll('img').forEach(i=>i.loading='eager');await Promise.all([...document.images].map(i=>i.decode().catch(()=>null)));const a=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}});return {broken:[...document.images].filter(i=>!i.naturalWidth).length,overflow:document.documentElement.scrollWidth>innerWidth+1,violations:a.violations.map(v=>v.id),incomplete:a.incomplete.map(v=>v.id)}}")
   r['pages'].append(dict(file=file,width=width,**result));page.screenshot(path=str(out/f'{file}-{width}.png'),full_page=file=='index.html')
 for preset in ['lime','coral','cyan']:
  for lang,theme in [('en','light'),('es','dark')]:
   page.set_viewport_size({'width':390,'height':900});page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen='dashboard',preset=preset,lang=lang,theme=theme)));page.evaluate('document.fonts.ready')
   a11y=page.evaluate("async()=>{const a=await axe.run(document);return a.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}")
   r['contrast_review'].append(dict(preset=preset,lang=lang,incomplete=a11y))
   page.evaluate("()=>{document.querySelector('.hero-copy h2').textContent='Coastlines: the Atlantic — Original programme title with a very long subtitle / Título original conservado con información adicional';document.querySelector('.hero-copy .primary').textContent='Ver el canal seleccionado con su nombre original';}")
   r['long_content'].append(dict(preset=preset,lang=lang,overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+1')))
 b.close()
r['summary']={'static_cases':len(r['pages']),'static_failures':sum(bool(x['broken'] or x['overflow'] or x['violations']) for x in r['pages']),'long_content_cases':len(r['long_content']),'long_content_failures':sum(x['overflow'] for x in r['long_content']),'errors':len(r['errors']),'blocked':len(r['blocked']),'console':len(r['console'])}
(out/'pages-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['summary'],indent=2));raise SystemExit(any(r['summary'][k] for k in ['static_failures','long_content_failures','errors','blocked','console']))
