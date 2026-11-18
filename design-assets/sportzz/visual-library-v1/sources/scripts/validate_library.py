from pathlib import Path
import json, hashlib, io, threading, functools, os, socket, re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from PIL import Image
import numpy as np
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];P=R/'assets/magnific/previews';M=R/'assets/magnific/manifests'
V=json.loads((M/'sportzz-visual-assets.json').read_text());I=json.loads((R/'assets/icons/icon-manifest.json').read_text())
report={'collection':'SPORTZZ Visual Asset Library 1.0','date':'2026-11-09','scope':'Standalone asset collection; not application or CI validation','checks':{},'browser':{},'limitations':V['pending']}
assert len(V['assets'])==21
assert [sum(a['category']==x for a in V['assets']) for x in ['photography','mockups','graphics']]==[8,8,5]
assert len(I['icons'])==70
assert len(set(a['id'] for a in I['icons']))==70
expected={
'navigation':'home menu arrow-left arrow-right arrow-up arrow-down chevron-left chevron-right chevron-up chevron-down close external-link breadcrumb'.split(),
'actions':'plus minus edit trash save copy download upload refresh search filter sort-ascending sort-descending more-horizontal settings share link eye eye-off'.split(),
'status':'check check-circle alert-triangle alert-circle info help-circle clock loader x-circle pause-circle'.split(),
'data':'database server network terminal file file-text code layers activity chart-line chart-bar list grid table calendar history'.split(),
'media':'play pause stop volume volume-off fullscreen trophy football basketball tennis racing-flag whistle'.split()}
assert {(a['family'],a['id']) for a in I['icons']}=={(fam,n) for fam,ns in expected.items() for n in ns}
hashes=[]
for e in I['icons']:
    path=R/e['path'];root=ET.parse(path).getroot()
    assert root.attrib['viewBox']=='0 0 24 24'
    for key,val in [('stroke','currentColor'),('stroke-width','1.75'),('fill','none'),('stroke-linecap','round'),('stroke-linejoin','round')]:assert root.attrib[key]==val
    assert all(el.tag.split('}')[-1] in ['svg','path'] for el in root.iter())
    assert len(list(root))==1
    hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
assert len(set(hashes))==70
sprite=ET.parse(R/'assets/icons/sprite.svg').getroot();ids=[e.attrib['id'] for e in sprite]
assert len(ids)==len(set(ids))==70 and set(ids)=={e['id'] for e in I['icons']}
for sym in sprite:
    assert sym.attrib['stroke']=='currentColor' and sym.attrib['stroke-width']=='1.75'
    e=next(a for a in I['icons'] if a['id']==sym.attrib['id'])
    assert list(sym)[0].attrib['d']==list(ET.parse(R/e['path']).getroot())[0].attrib['d']
report['checks'].update({'primary_assets':21,'photography':8,'mockups':8,'graphics':5,'independent_svg_icons':70,'unique_sprite_ids':70,'no_duplicate_icon_files':True,'svg_no_raster_filters_scripts':True,'stroke_and_currentColor':True,'sprite_matches_individual_files':True})
for a in V['assets']:
    for key in ['id','name','category','description','prompt','resolution','format','ratio','usage','alt','notes','review_status','status']:assert key in a,(a['id'],key)
    assert (R/a['path']).is_file()
    if a['format']=='webp':
        im=Image.open(R/a['path']);assert im.format=='WEBP' and list(im.size)==a['resolution']
        if a['category']=='photography':assert im.size==((2400,1350) if a['id']=='PHOTO-01' else (2048,1152))
        if a['category']=='mockups':assert max(im.size)>=2000
        for v in a.get('responsive_variants',[]):assert list(Image.open(R/v['path']).size)==v['resolution']
    for p in a.get('components',[]):assert (R/p).is_file()
for p in (R/'assets/magnific').rglob('*'):
    if p.suffix in ['.png','.jpg','.webp']:
        with Image.open(p) as im:im.verify()
tile=Image.open(R/'assets/magnific/graphics/textures/sportzz-graphic-carbon-texture-tile.webp');a=np.asarray(tile)
assert np.array_equal(a[:,0],a[:,-1]) and np.array_equal(a[0],a[-1])
pat=ET.parse(R/'assets/magnific/graphics/patterns/sportzz-graphic-diagonal-pattern-18deg.svg').getroot()
import math
th=float(pat.attrib['viewBox'].split()[-1]);assert abs(math.degrees(math.atan(64/th))-18)<1e-7
cut_angles=[]
for path in (R/'assets/magnific/graphics/patterns').glob('sportzz-graphic-signal-cut-*-18deg.svg'):
    d=list(ET.parse(path).getroot())[0].attrib['d'];tokens=re.findall(r'[MLHVZ]|-?\d+(?:\.\d+)?',d)
    j=0;pos=(0.,0.);start=None;segments=[]
    while j<len(tokens):
        cmd=tokens[j];j+=1
        if cmd in ['M','L']:
            dest=(float(tokens[j]),float(tokens[j+1]));j+=2
        elif cmd=='H':dest=(float(tokens[j]),pos[1]);j+=1
        elif cmd=='V':dest=(pos[0],float(tokens[j]));j+=1
        elif cmd=='Z':dest=start
        else:raise AssertionError(cmd)
        if cmd=='M':start=dest
        else:segments.append((pos,dest))
        pos=dest
    for p,q in segments:
        dx,dy=abs(p[0]-q[0]),abs(p[1]-q[1])
        if dx>1e-7 and dy>1e-7:
            angle=math.degrees(math.atan(dx/dy));assert abs(angle-18)<1e-7,(path,angle);cut_angles.append(angle)
report['checks'].update({'required_web_resolutions':True,'all_images_decode':True,'manifests_required_fields':True,'tile_opposite_edges_identical':True,'pattern_angle_degrees_from_vertical':18,'all_runtime_paths_exist':True})
report['checks']['signal_cut_diagonal_segments_verified']=len(cut_angles)
class Links(HTMLParser):
    def __init__(self):super().__init__();self.urls=[]
    def handle_starttag(self,tag,attrs):
        for key,val in attrs:
            if key in ['href','src'] and val and not val.startswith('#'):self.urls.append(val)
l=Links();l.feed((R/'index.html').read_text())
for url in l.urls:
    assert not url.startswith(('http:','https:'))
    path=url.split('#')[0]
    if path:assert (R/path).is_file(),path
report['checks']['html_local_links_checked']=len(l.urls)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
port=8766
server=ThreadingHTTPServer(('0.0.0.0',port),functools.partial(Quiet,directory=str(R)))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
errors=[];failed=[];browser=None
try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/home/designer/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',headless=True,args=['--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.on('response',lambda r:failed.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
        page.goto(f'http://127.0.0.1:{port}',wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        page.locator('img').evaluate_all("els=>els.forEach(e=>e.loading='eager')")
        page.wait_for_function("[...document.images].every(e=>e.complete && e.naturalWidth>0)")
        assert page.locator('.icon').count()==70
        assert page.evaluate('document.documentElement.scrollWidth')<=1440
        page.screenshot(path=str(P/'sportzz-preview-catalog-desktop-1440x900.png'))
        page.locator('#icons').scroll_into_view_if_needed()
        page.locator('#search').fill('football');assert page.locator('.icon:visible').count()==1
        page.locator('#search').fill('');assert page.locator('.icon:visible').count()==70
        page.locator('#theme').click()
        assert page.locator('.icon').first.evaluate('e=>getComputedStyle(e).color')=='rgb(8, 11, 9)'
        page.locator('#theme').click()
        for size in [16,20,24,32]:
            page.locator('#size').select_option(str(size))
            assert all(int(r)==size for r in page.locator('.icon svg').evaluate_all('els=>els.map(e=>e.getBoundingClientRect().width)'))
        # Pixel test external-symbol inheritance for EVERY icon, not only computed parent styles.
        page.add_style_tag(content='.icon {color:rgb(255,51,153)!important}')
        pixel_counts={}
        for idx,name in enumerate(ids):
            el=page.locator('.icon svg').nth(idx)
            raw=el.screenshot();arr=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'))
            pixels=((arr[:,:,0]>190)&(arr[:,:,1]<120)&(arr[:,:,2]>90)).sum()
            assert pixels>4,(idx,name,pixels)
            pixel_counts[name]=int(pixels)
        page.locator('style').last.evaluate('el=>el.remove()')
        page.locator('#size').select_option('24')
        page.locator('#icons').scroll_into_view_if_needed()
        page.screenshot(path=str(P/'sportzz-preview-catalog-icons-desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.evaluate('scrollTo(0,0)');page.evaluate('document.fonts.ready')
        assert page.evaluate('document.documentElement.scrollWidth')<=390
        page.screenshot(path=str(P/'sportzz-preview-catalog-mobile-390x844.png'))
        assert not errors,errors
        assert not failed,failed
        report['browser']={'engine':'isolated VM Chromium 1234','desktop':[1440,900],'mobile':[390,844],'console_errors':errors,'http_errors':failed,'horizontal_overflow':False,'search_filter_pass':True,'theme_toggle_pass':True,'sizes_pass':[16,20,24,32],'external_sprite_symbols_pixel_validated':len(pixel_counts),'external_sprite_pixel_counts':pixel_counts,'screenshots':[str(p.relative_to(R)) for p in P.glob('sportzz-preview-catalog*.png')],'temporary_port':port,'pid':os.getpid()}
        browser.close();browser=None
finally:
    if browser:
        try:browser.close()
        except Exception:pass
    server.shutdown();server.server_close();thread.join(timeout=5)
    sock=socket.socket();assert sock.connect_ex(('127.0.0.1',port))!=0;sock.close()
    report['temporary_services_stopped']=True
report['status']='passed'
(M/'sportzz-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'status':'passed','primary_assets':21,'icons':70,'sprite_ids':70,'external_sprite_pixel_tests':70,'console_errors':0,'horizontal_overflow':False,'temporary_services_stopped':True},indent=2))
