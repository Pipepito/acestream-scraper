from pathlib import Path
import json,subprocess,zipfile,hashlib,re,urllib.request,shutil
from PIL import Image
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];P=R/'previews'
report=json.loads((R/'validation.json').read_text())
assert len(report['outputs'])==5
for e in report['outputs'].values():assert e['frames']==240 and e['duration_seconds']==10
result=subprocess.run(['/usr/bin/ffmpeg','-hide_banner','-i',str(R/'sportzz-brand-promo-10s-master.mp4'),'-af','ebur128=peak=true','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
text=result.stderr.decode(errors='replace')
(R/'source/audio/sportzz-audio-loudness-measurement.txt').write_text(text)
summ=text.rsplit('Summary:',1)[-1]
report['audio_loudness_summary']=summ.strip()
html='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SPORTZZ — Brand promo / 10s</title><style>
*{box-sizing:border-box}body{margin:0;background:#080B09;color:#F5F7F3;font-family:system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:28px 24px}header{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:24px}header img{width:150px;height:auto}header span{font-size:12px;color:#AFB8B0}video{display:block;width:100%;aspect-ratio:16/9;background:#080B09;border:1px solid #263129;border-radius:4px}h1{font-size:21px;letter-spacing:-.025em;margin:23px 0 9px}p{font-size:14px;line-height:1.6;color:#AFB8B0}.links{display:flex;flex-wrap:wrap;gap:12px;margin-top:24px}a{color:#F5F7F3;text-underline-offset:4px}a:focus-visible{outline:2px solid #B6FF00;outline-offset:4px}.links a{padding:12px 18px;border:1px solid #38433B;border-radius:6px;font-size:13px;text-decoration:none}.links a:first-child{background:#B6FF00;color:#080B09;border-color:#B6FF00;font-weight:600}.note{margin-top:22px;font-size:12px}details{margin-top:26px;color:#AFB8B0;font-size:13px}details img{width:100%;margin-top:18px}@media(max-width:600px){main{padding:24px 18px}header{align-items:flex-start;flex-direction:column}h1{font-size:19px}.links a{flex:1 1 44%;text-align:center}}
</style></head><body><main><header><img src="sportzz-logotipo.svg" alt="SPORTZZ"><span>BRAND PROMO · 10,000 s · 720p · 24 fps</span></header><video id="promo" controls playsinline preload="auto" poster="sportzz-brand-promo-poster.webp"><source src="sportzz-brand-promo-10s-web.mp4" type="video/mp4">Tu navegador no admite este vídeo. Usa los enlaces de descarga.</video><h1>EL DEPORTE. SIN PAUSA.</h1><p>Voz en español de España, diseño sonoro y marca original compuesta en postproducción. Interfaz conceptual, sin competiciones ni programación inventadas.</p><div class="links"><a href="sportzz-brand-promo-10s-master.mp4" download>Descargar máster con voz</a><a href="sportzz-brand-promo-10s-web.mp4" download>MP4 web</a><a href="sportzz-brand-promo-10s-silent.mp4" download>MP4 sin sonido</a><a href="sportzz-brand-promo-10s-clean.mp4" download>Versión limpia</a><a href="sportzz-brand-promo-10s-web.webm" download>WebM sin sonido</a><a href="sportzz-brand-promo-10s-delivery.zip" download>Paquete completo</a></div><p class="note">Resolución 1280 × 720 solicitada para esta entrega. Revisión de concepto: comprobar derechos y semejanzas antes de uso comercial; sustituir la interfaz por capturas reales cuando estén disponibles.</p><details><summary>Ver fotogramas del montaje</summary><img src="sportzz-brand-promo-storyboard.webp" alt="Secuencia de dieciséis fotogramas con tiempos del anuncio"></details></main></body></html>'''
html=html.replace('<a href="sportzz-brand-promo-10s-delivery.zip" download>Paquete completo</a>','')
html=html.replace('</head>','<link rel="icon" type="image/svg+xml" href="sportzz-logotipo.svg"></head>')
html=html.replace('</body>', '''<script>
// Load the short preview into a local Blob so seeking also works on a simple
// temporary transfer server without HTTP Range support. Download links stay direct.
fetch('sportzz-brand-promo-10s-web.mp4').then(r=>{if(!r.ok)throw new Error('Video download failed');return r.blob()}).then(blob=>{const v=document.querySelector('#promo');v.src=URL.createObjectURL(blob);v.load();v.dataset.blobReady='true'}).catch(e=>console.error(e));
</script></body>''')
(R/'index.html').write_text(html)
shutil.copy2(R/'source/brand/logotipo-blanco.svg',R/'sportzz-logotipo.svg')
shutil.copy2(P/'sportzz-brand-promo-storyboard.webp',R/'sportzz-brand-promo-storyboard.webp')
stage=Path('/tmp/opencode/sportzz-download-20261109/promo');stage.mkdir(exist_ok=True)
names=list(report['outputs'])+['sportzz-brand-promo-poster.webp','index.html','README.md']
for name in names:
    p=stage/name
    if not p.exists():p.symlink_to(R/name)
for name,target in [('sportzz-logotipo.svg',R/'source/brand/logotipo-blanco.svg'),('sportzz-brand-promo-storyboard.webp',P/'sportzz-brand-promo-storyboard.webp')]:
    p=stage/name
    if not p.exists():p.symlink_to(target)
base='http://127.0.0.1:8767/promo/'
errors=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/home/designer/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome',headless=True,args=['--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
    page.goto(base,wait_until='networkidle');video=page.locator('#promo')
    page.wait_for_function('document.querySelector("video").dataset.blobReady==="true" && document.querySelector("video").readyState>=2')
    assert abs(video.evaluate('v=>v.duration')-10)<.001
    assert video.evaluate('v=>v.videoWidth')==1280 and video.evaluate('v=>v.videoHeight')==720
    snapshots=[]
    for t,label in [(2.35,'sports'),(5.4,'experience'),(9.0,'brand')]:
        video.evaluate('(v,t)=>{v.pause();v.currentTime=t}',t)
        page.wait_for_function('(t)=>Math.abs(document.querySelector("video").currentTime-t)<.05 && !document.querySelector("video").seeking',arg=t)
        video.screenshot(path=str(P/f'sportzz-video-player-{label}.png'));snapshots.append(label)
    # Actual browser playback, not only metadata parsing.
    video.evaluate('v=>{v.currentTime=0;v.muted=true;return v.play()}')
    page.wait_for_function('document.querySelector("video").currentTime>.75')
    video.evaluate('v=>{v.pause();v.currentTime=9}')
    page.wait_for_function('!document.querySelector("video").seeking')
    page.screenshot(path=str(P/'sportzz-promo-review-desktop-1440x900.png'))
    page.set_viewport_size({'width':390,'height':844});page.evaluate('scrollTo(0,0)')
    assert page.evaluate('document.documentElement.scrollWidth')<=390
    page.screenshot(path=str(P/'sportzz-promo-review-mobile-390x844.png'))
    assert not errors,errors
    report['browser_review']={'engine':'isolated VM Chromium','duration':10,'resolution':[1280,720],'playback_pass':True,'seek_states':snapshots,'console_errors':errors,'desktop':[1440,900],'mobile':[390,844],'horizontal_overflow':False,'browser_closed':True,'download_server':'Existing user-requested temporary transfer server reused, port 8767, PID 353545; remains open for the active download/review.'}
    browser.close()
report['editorial_review']={'note':'Internal review of sampled frames; synthetic scenes and local shoe texture smoothing remain subject to owner creative approval. Not an anatomical or rights certification.','commercial_clearance':'pending','conceptual_ui_replacement':'pending'}
(R/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
generation=json.loads((R/'generation.json').read_text());assert generation['total_credits']==4428
files=[]
for p in R.rglob('*'):
    if not p.is_file() or p.suffix in ['.zip','.pyc'] or 'work' in p.relative_to(R).parts or '__pycache__' in p.parts:continue
    if p.name=='file-manifest.json':continue
    # Keep the unretouched AI source (with its unwanted third-party shoe mark)
    # on the VM only. Do not ship it in the final commercial-asset download.
    if p.name=='sportzz-generated-source-preview.mp4':continue
    if p.parent==P and not p.name.startswith(('sportzz-promo-frame-','sportzz-brand-promo-storyboard','sportzz-video-player-','sportzz-promo-review-')):continue
    files.append(p)
manifest={'files':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(files)]}
(R/'file-manifest.json').write_text(json.dumps(manifest,indent=2));files.append(R/'file-manifest.json')
out=R/'sportzz-brand-promo-10s-delivery.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,Path('sportzz-brand-promo-10s')/p.relative_to(R))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
p=stage/out.name
if not p.exists():p.symlink_to(out)
for host in ['192.168.1.144','10.253.0.20']:
    url=f'http://{host}:8767/promo/{out.name}'
    with urllib.request.urlopen(urllib.request.Request(url,method='HEAD'),timeout=10) as response:assert response.status==200 and int(response.headers['Content-Length'])==out.stat().st_size
print(json.dumps({'delivery_zip_mb':round(out.stat().st_size/1048576,2),'mp4_exports':4,'webm_exports':1,'frames_per_export':240,'fps':24,'duration_seconds':10,'credits':4428,'review_url_lan':'http://192.168.1.144:8767/promo/','review_url_vpn':'http://10.253.0.20:8767/promo/'},indent=2))
