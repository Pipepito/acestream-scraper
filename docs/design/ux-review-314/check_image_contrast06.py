"""Measure text against the rendered image background with glyphs hidden.

This resolves the image/pseudo-element cases axe cannot calculate. Synthetic
local fixtures only. It is not a general accessibility conformance assertion.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote, urlencode
from io import BytesIO
import argparse, json, mimetypes, math, re
from PIL import Image
from playwright.sync_api import sync_playwright

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args()
root=Path(__file__).resolve().parent;out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
report={'cases':[],'blocked':[],'errors':[]}
def luminance(rgb):
    values=[x/255 for x in rgb[:3]]
    return sum((v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4)*w for v,w in zip(values,[.2126,.7152,.0722]))
with sync_playwright() as p:
    browser=p.chromium.launch();c=browser.new_context(service_workers='block',reduced_motion='reduce',device_scale_factor=1)
    def intercept(route):
        u=urlsplit(route.request.url);f=(root/unquote(u.path).lstrip('/')).resolve()
        if u.hostname!='design.invalid' or route.request.method!='GET' or not f.is_relative_to(root) or not f.is_file():
            report['blocked'].append(u.path);route.abort();return
        route.fulfill(body=f.read_bytes(),content_type=mimetypes.guess_type(f.name)[0] or 'text/plain')
    c.route('**/*',intercept);page=c.new_page();page.on('pageerror',lambda e:report['errors'].append(str(e)))
    for preset in ['lime','coral','cyan']:
        for lang,theme in [('en','light'),('es','dark')]:
            for width in [320,390,820,1440]:
                page.set_viewport_size({'width':width,'height':1200})
                page.goto('http://design.invalid/workflow-prototype.html?'+urlencode(dict(screen='dashboard',preset=preset,lang=lang,theme=theme)))
                page.evaluate('document.fonts.ready');page.locator('.watch-hero img').evaluate('(e)=>e.decode()')
                boxes=page.evaluate("""()=>{
                    const hero=document.querySelector('.watch-hero'), h=hero.getBoundingClientRect(), result=[];
                    for(const e of hero.querySelectorAll('.hero-copy .eyebrow,.hero-copy h2,.hero-copy>p,.hero-copy .button,.art-label')){
                        if(!e.getClientRects().length)continue;
                        const s=getComputedStyle(e), walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);
                        while(walker.nextNode()){
                            const n=walker.currentNode;if(!n.textContent.trim())continue;
                            const r=document.createRange();r.selectNodeContents(n);
                            for(const b of r.getClientRects())if(b.width&&b.height)result.push({text:n.textContent.trim(),color:s.color,x:b.x-h.x,y:b.y-h.y,w:b.width,h:b.height,required:parseFloat(s.fontSize)>=24?3:4.5});
                        }
                    }
                    hero.querySelectorAll('*').forEach(e=>{e.style.setProperty('color','transparent','important');e.style.setProperty('text-shadow','none','important')});
                    return result;
                }""")
                background=Image.open(BytesIO(page.locator('.watch-hero').screenshot())).convert('RGB')
                measures=[]
                for box in boxes:
                    rgb=list(map(float,re.findall(r'[\d.]+',box['color'])[:3]));fg=luminance(rgb)
                    bounds=(max(0,math.ceil(box['x'])),max(0,math.ceil(box['y'])),min(background.width,math.floor(box['x']+box['w'])),min(background.height,math.floor(box['y']+box['h'])))
                    pixels=background.crop(bounds).get_flattened_data()
                    ratios=[(max(fg,luminance(v))+.05)/(min(fg,luminance(v))+.05) for v in set(pixels)]
                    minimum=min(ratios);measures.append(dict(text=box['text'],ratio=round(minimum,3),required=box['required'],passed=minimum>=box['required']))
                report['cases'].append(dict(preset=preset,lang=lang,theme=theme,width=width,measures=measures))
    browser.close()
measures=[m for c in report['cases'] for m in c['measures']]
report['summary']=dict(contexts=len(report['cases']),text_rectangles=len(measures),failures=sum(not m['passed'] for m in measures),minimum_ratio=min(m['ratio'] for m in measures),blocked=len(report['blocked']),errors=len(report['errors']))
(out/'image-contrast-checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
raise SystemExit(bool(report['summary']['failures'] or report['blocked'] or report['errors']))
