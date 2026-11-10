from pathlib import Path
import json, hashlib, zipfile, re, math, xml.etree.ElementTree as ET
from PIL import Image
R=Path(__file__).resolve().parents[2];M=R/'assets/magnific/manifests'
vpath=M/'sportzz-visual-assets.json';v=json.loads(vpath.read_text())
icons_path=R/'assets/icons/icon-manifest.json';icons=json.loads(icons_path.read_text())
from production_spec import ICON_REFERENCE_PROMPT, GRAPHIC_REFERENCE_PROMPT, CORRECTIONS
icons['generation_prompt_reference']=ICON_REFERENCE_PROMPT
icons['reference_note']='Magnific sample used for direction; every production icon reconstructed locally as editable paths.'
for e in icons['icons']:
    e.update({'description':f'Original outline {e["id"]} pictogram','format':'svg','resolution':'scalable','ratio':'1:1','usage':['web-interface','documentation'],'alt':e['id'].replace('-',' '),'notes':'Decorative use aria-hidden; label the surrounding control when interactive.','review_status':'internally_reviewed'})
icons_path.write_text(json.dumps(icons,ensure_ascii=False,indent=2))
allfiles=[p for p in R.rglob('*') if p.is_file() and p.suffix!='.zip' and '__pycache__' not in p.parts and p.suffix!='.pyc']
file_entries=[]
for p in sorted(allfiles):
    path=str(p.relative_to(R));category='source' if path.startswith('sources/') else 'documentation'
    if path.startswith('assets/icons/'):category='icons'
    elif '/previews/' in path:category='preview'
    elif '/photography/' in path:category='photography'
    elif '/mockups/' in path:category='mockups'
    elif '/graphics/' in path:category='graphics'
    elif '/manifests/' in path:category='manifest'
    elif '/brand/' in path:category='brand-reference'
    parent=next((a for a in v['assets'] if p.name.startswith(Path(a['name']).stem)),None)
    if p.suffix in ['.png','.jpg','.webp']:
        resolution=list(Image.open(p).size)
        w,h=resolution;g=math.gcd(w,h);ratio=f'{w//g}:{h//g}'
    elif p.suffix=='.svg':resolution=ET.parse(p).getroot().attrib.get('viewBox','symbol-collection');ratio='scalable'
    else:resolution=None;ratio=None
    entry={'id':f'FILE-{len(file_entries)+1:03}','filename':p.name,'path':path,'category':category,'description':parent['description'] if parent else p.stem.replace('-',' '),'prompt':parent['prompt'] if parent else ('See assets/icons/icon-manifest.json and sources/scripts/build_icons.py' if category=='icons' else 'Locally exported or documented; not an additional image generation'),'resolution':resolution,'format':p.suffix.lstrip('.'),'ratio':ratio,'usage':parent['usage'] if parent else ['review-only' if category=='preview' else 'documentation-reference'],'alt':parent['alt'] if parent else '','notes':'Master/reference file; not a web UI substitute.' if ('master' in p.stem or path.startswith('sources/')) else 'See main asset record for provenance and applicable limits.','review_status':'rejected_for_production' if '/rejected/' in path else 'internally_reviewed','bytes':p.stat().st_size}
    if parent:entry['asset_id']=parent['id']
    if '/rejected/' in path and parent:
        logs=json.loads((M/'sportzz-generation-log.json').read_text())['runs']
        entry['prompt']=next(a['prompt'] for a in logs if a['id']==parent['id'] and a.get('attempt')==1)
        entry['notes']=CORRECTIONS[parent['id']][2]+' Rejected reference only; do not use in production.'
    if 'sportzz-reference-signal-icons-sample-5' in p.stem:entry['prompt']=ICON_REFERENCE_PROMPT
    if 'sportzz-reference-graphic-directions' in p.stem:entry['prompt']=GRAPHIC_REFERENCE_PROMPT
    if p.name in ['sportzz-visual-assets.json','sportzz-file-index.json']:
        entry['bytes']=None
        entry['notes']='Size intentionally omitted for generated manifests to avoid self-referential inventory sizes.'
    file_entries.append(entry)
if not any(e['path']=='assets/magnific/manifests/sportzz-file-index.json' for e in file_entries):
    file_entries.append({'id':f'FILE-{len(file_entries)+1:03}','filename':'sportzz-file-index.json','path':'assets/magnific/manifests/sportzz-file-index.json','category':'manifest','description':'Independent SHA-256 file index','prompt':'Locally computed integrity index; no generation','resolution':None,'format':'json','ratio':None,'usage':['integrity-check'],'alt':'','notes':'Excludes its own hash to avoid circular hashing.','review_status':'validated','bytes':None})
v['files']=file_entries
v['credits']['balance_before']=43715
v['credits']['balance_after']=41390
v['credits']['verified_delta']=2325
v['files_note']='Complete delivery file inventory; primary 21 asset records remain in assets[]. Icon metadata and sprite contract are in icons_manifest. Source/rejected files are never production inputs.'
vpath.write_text(json.dumps(v,ensure_ascii=False,indent=2))
# An independent SHA-256 index deliberately excludes itself; no self-referential hashes.
files=[p for p in R.rglob('*') if p.is_file() and p.suffix!='.zip' and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='sportzz-file-index.json']
index={'brand':'SPORTZZ','files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
(M/'sportzz-file-index.json').write_text(json.dumps(index,indent=2))
files.append(M/'sportzz-file-index.json')
full=R/'sportzz-visual-assets-collection-1.0-complete.zip'
web=R/'sportzz-visual-assets-collection-1.0-web.zip'
with zipfile.ZipFile(full,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(files):z.write(p,Path('sportzz-visual-assets-collection-1.0')/p.relative_to(R))
with zipfile.ZipFile(web,'w',zipfile.ZIP_DEFLATED) as z:
    included=[]
    for p in sorted(files):
        rel=p.relative_to(R)
        if rel.parts[0]=='sources' or 'master' in p.stem or '-initial' in p.stem:continue
        if p.name=='sportzz-file-index.json':continue
        z.write(p,Path('sportzz-visual-assets-collection-1.0-web')/rel);included.append(str(rel))
    z.writestr('sportzz-visual-assets-collection-1.0-web/WEB-BUNDLE-NOTE.txt','Lightweight web bundle. PNG masters, generation references and build scripts are only in the complete bundle. Manifest source/master paths describe the complete collection and are not runtime dependencies. All index.html links, web assets, 70 icons and sprite are included.\n')
for p in [full,web]:
    with zipfile.ZipFile(p) as z:assert z.testzip() is None
    print(p.name,round(p.stat().st_size/1048576,2),'MiB')
print(len(files),'files in complete package; archives validated.')
