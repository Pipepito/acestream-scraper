"""Check design links/fragments, generated drift, coverage and synthetic boundaries."""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
import argparse, hashlib, json, re, subprocess, sys, unicodedata

ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
OUT=Path(args.output);OUT.mkdir(parents=True,exist_ok=True)
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ['href','src'] and v:self.links.append(v)
   if k=='id' and v:self.ids.add(v)
def anchors(path):
 text=path.read_text();p=Parser();p.feed(text);found=p.ids
 # Templates render main at runtime; runtime checks verify one main on every view.
 templates=text
 if path.name=='workflow-prototype.html':templates+='\n'+(ROOT/'workflow-engine.js').read_text()
 found.update(re.findall(r'''\bid=[\"']([a-zA-Z][\w-]*)[\"']''',templates))
 if path.suffix=='.md':
  counts={}
  for heading in re.findall(r'^#{1,6}\s+(.+)',text,re.M):
   slug=re.sub(r'[^\w\s-]','',re.sub(r'<[^>]+>','',heading.lower())).replace(' ','-')
   count=counts.get(slug,0);counts[slug]=count+1;found.add(slug+('-'+str(count) if count else ''))
 return found
links=[];failures=[];fragments=0
for path in ROOT.iterdir():
 if path.suffix=='.html':
  p=Parser();p.feed(path.read_text());links.extend((path,x) for x in p.links)
 elif path.suffix=='.md':links.extend((path,x) for x in re.findall(r'\]\(([^ )]+)',path.read_text()))
 elif path.suffix=='.css':links.extend((path,x) for x in re.findall(r'url\([\'"]?([^\'")]+)',path.read_text()))
cache={};local=0
for origin,ref in links:
 u=urlsplit(ref)
 if u.scheme or ref.startswith('{'):continue
 target=(origin.parent/unquote(u.path)).resolve() if u.path else origin
 local+=1
 if not target.exists():failures.append(f'{origin.name}: missing {ref}');continue
 if u.fragment and target.suffix in ['.html','.md']:
  fragments+=1
  if target not in cache:cache[target]=anchors(target)
  if unquote(u.fragment) not in cache[target]:failures.append(f'{origin.name}: missing fragment {ref}')
generated=['workflow-data.js','workflow-data.json','workflow-specification.md','traceability-matrix.md','source-contracts.md','source-control-map.md','workflow-gallery.html']
before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in generated}
result=subprocess.run([sys.executable,str(ROOT/'compose_workflows.py')],capture_output=True,text=True)
if result.returncode:failures.append('Generator failed: '+result.stderr)
after={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in generated}
drift=[p for p in generated if before[p]!=after[p]]
if drift:failures.append('Generated drift: '+str(drift))
data=json.loads((ROOT/'workflow-data.json').read_text());screens=data['screens']
export_names={p.name for p in (ROOT/'workflow-exports').glob('*.jpg')}
expected={s['id']+'-'+lang+'.jpg' for s in screens for lang in ['en','es']}
if export_names!=expected:failures.append('Export inventory mismatch '+str(sorted(export_names^expected)))
if '**RECONCILE BEFORE HANDOFF**' in (ROOT/'source-control-map.md').read_text():failures.append('Unmapped input/dialog module')
runtime_keys={f['key'] for s in screens if s['family']=='runtime' for b in s['blocks'] for f in b.get('fields',[])}
if len(runtime_keys)!=47:failures.append('Runtime coverage differs from 47 options')
engine=(ROOT/'workflow-engine.js').read_text()
if re.search(r'\b(fetch|XMLHttpRequest|WebSocket)\s*\(',engine):failures.append('Unexpected network API in synthetic engine')
if re.search(r'(localStorage|sessionStorage)\s*\.',engine):failures.append('Unexpected browser persistence in synthetic engine')
node=subprocess.run(['node','--check',str(ROOT/'workflow-engine.js')],capture_output=True,text=True)
if node.returncode:failures.append(node.stderr)
report=dict(local_links=local,local_fragments=fragments,generated_files=len(generated),generated_drift=drift,screens=len(screens),exports=len(export_names),runtime_fields=len(runtime_keys),failures=failures)
(OUT/'artifact-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
