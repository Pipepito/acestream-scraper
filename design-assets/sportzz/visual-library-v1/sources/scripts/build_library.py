from pathlib import Path
import json, math, io, shutil, html, hashlib
from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np
import cv2, cairosvg
from production_spec import *
R=Path(__file__).resolve().parents[2];A=R/'assets/magnific';P=A/'previews';M=A/'manifests'
for folder in ['graphics/patterns','graphics/textures','graphics/backgrounds','photography/hero','photography/sports','photography/editorial','mockups/devices','mockups/broadcast','mockups/brand-applications','previews','manifests']:(A/folder).mkdir(parents=True,exist_ok=True)
assets=[];runs=[]
def rel(p):return str(p.relative_to(R))
def dims(p):return list(Image.open(p).size)
def export(im,path,size):
    im=ImageOps.fit(im.convert('RGB'),size,method=Image.Resampling.LANCZOS)
    im.save(path,quality=88,method=6)
    return im
def add(id,name,cat,description,alt,prompt,creation,master,size,usage,notes='',source='Magnific / Google Nano Banana 2'):
    path=master.with_name(name+'.webp')
    im=Image.open(master).convert('RGB')
    if id=='MOCKUP-08':
        a=np.asarray(im).copy();mask=((a[:,:,1]>a[:,:,0]*.93)&(a[:,:,0]<a[:,:,1]*1.12)&(a[:,:,2]<a[:,:,1]*.94)&(a[:,:,1]>65)).astype('uint8')*255
        mask[:,:int(im.width*.53)]=0;mask[int(im.height*.78):]=0
        mask=cv2.dilate(mask,np.ones((5,5),np.uint8))
        a=cv2.inpaint(a,mask,5,cv2.INPAINT_TELEA);im=Image.fromarray(a)
        im.save(master.with_name(name+'-compositing-master.png'))
        Image.fromarray(mask).save(R/'sources/magnific-references/sportzz-mask-physical-kit-cleanup.png')
        notes+=' Local masked inpainting removes generated lime pseudo-marks on lanyard; original PNG unchanged.'
    if id=='GRAPHIC-03':
        small=im.resize((1024,1024),Image.Resampling.LANCZOS)
        tile=Image.new('RGB',(2048,2048));tile.paste(small,(0,0));tile.paste(ImageOps.mirror(small),(1024,0));tile.paste(ImageOps.flip(small),(0,1024));tile.paste(ImageOps.flip(ImageOps.mirror(small)),(1024,1024))
        im=tile;im.save(master.with_name(name+'-seamless-master.png'))
        # Lossless WebP preserves exact seam equality.
        im.save(path,lossless=True,method=6)
        a=np.asarray(im);assert np.array_equal(a[:,0],a[:,-1]) and np.array_equal(a[0],a[-1])
        notes+=' Seamless derivative constructed by mirror tiling; opposite edge pixels verified equal. WebP encoded losslessly.'
    else:im=export(im,path,size)
    variants=[]
    if cat in ['photography','mockups']:
        for width in [640,1280]:
            h=round(width*size[1]/size[0]);v=path.with_name(name+f'-{width}w.webp');export(im,v,(width,h));variants.append({'path':rel(v),'resolution':[width,h],'format':'webp'})
    info={'id':id,'name':path.name,'path':rel(path),'category':cat,'description':description,'prompt':prompt,'resolution':dims(path),'format':'webp','ratio':f'{size[0]//math.gcd(*size)}:{size[1]//math.gcd(*size)}','usage':usage,'alt':alt,'notes':notes.strip(),'review_status':'internally_reviewed','status':['generated','exported','optimized','validated'],'master':{'path':rel(master),'resolution':dims(master),'format':'png','unchanged':True},'responsive_variants':variants,'source':{'generator':source,'creation_page':f'https://www.magnific.com/app/creation/{creation}','requested_resolution':'2k','credits':75,'seed':'not specified'},'commercial_clearance':'pending; AI-generated concept, not an actual event; no photographic rights or likeness clearance asserted'}
    if id in CORRECTIONS:info['generation_correction']=CORRECTIONS[id][2]
    if id=='MOCKUP-08':info['compositing_master']=rel(master.with_name(name+'-compositing-master.png'))
    if id=='GRAPHIC-03':info['seamless_master']=rel(master.with_name(name+'-seamless-master.png'))
    assets.append(info)
    return info

for i,(cat,slug,creation,desc,alt,prompt) in enumerate(PHOTO,1):
    id=f'PHOTO-{i:02}';name=f'sportzz-photo-{slug}-16x9';master=A/f'photography/{cat}/{name}-master.png'
    original_prompt=prompt+PHOTO_TAIL;final_prompt=CORRECTIONS[id][1] if id in CORRECTIONS else original_prompt
    creation=CORRECTIONS[id][0] if id in CORRECTIONS else creation
    add(id,name,'photography',desc,alt,final_prompt,creation,master,(2400,1350) if i==1 else (2048,1152),['hero','foundations'] if i==1 else ['sports-categories','editorial'],notes='Synthetic fictional sporting scene; no event attribution. Object-position should be reviewed for each crop.')
    runs.append({'id':id,'prompt':original_prompt,'attempt':1,'status':'rejected' if id in CORRECTIONS else 'accepted','credits':75})
    if id in CORRECTIONS:runs.append({'id':id,'prompt':final_prompt,'attempt':2,'status':'accepted','credits':75,'reason':CORRECTIONS[id][2]})
for i,(cat,slug,ratio,creation,desc,alt,prompt) in enumerate(MOCKUP,1):
    id=f'MOCKUP-{i:02}';name=f'sportzz-mockup-{slug}-{ratio}';master=A/f'mockups/{cat}/{name}-master.png'
    original_prompt=prompt+MOCKUP_TAIL;final_prompt=CORRECTIONS[id][1] if id in CORRECTIONS else original_prompt
    creation=CORRECTIONS[id][0] if id in CORRECTIONS else creation
    size={'16x9':(2048,1152),'4x5':(1600,2000),'4x3':(2048,1536)}[ratio]
    add(id,name,'mockups',desc,alt,final_prompt,creation,master,size,['screen-compositing' if i<8 else 'brand-compositing'],notes='Blank screen/surface. Synthetic hardware is generic, not a named manufacturer. Match screenshot corners manually; no exact display aspect ratio is guaranteed.')
    runs.append({'id':id,'prompt':original_prompt,'attempt':1,'status':'rejected' if id in CORRECTIONS else 'accepted','credits':75})
    if id in CORRECTIONS:runs.append({'id':id,'prompt':final_prompt,'attempt':2,'status':'accepted','credits':75,'reason':CORRECTIONS[id][2]})
for i,(cat,slug,creation,desc,alt,prompt) in enumerate(GRAPHIC,3):
    if i==5:continue
    name=f'sportzz-graphic-{slug}';add(f'GRAPHIC-{i:02}',name,'graphics',desc,alt,prompt,creation,A/f'graphics/{cat}/{name}-master.png',(2048,2048) if i==3 else (2048,1152),['subtle-background'])
    runs.append({'id':f'GRAPHIC-{i:02}','prompt':prompt,'status':'accepted_with_local_tile_processing' if i==3 else 'accepted','credits':75})

# Reconstruct precise editable geometry from the Magnific vector study.
angle=math.radians(18);tile_w=64;tile_h=tile_w/math.tan(angle)
paths=''.join(f'M{x} 0l-64 {tile_h:.9f}' for x in [-64,0,64,128,192])
pattern=f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="{tile_h:.9f}" viewBox="0 0 64 {tile_h:.9f}" fill="none"><path d="{paths}" stroke="#F5F7F3" stroke-opacity="0.035" stroke-width="1"/></svg>'
pat=A/'graphics/patterns/sportzz-graphic-diagonal-pattern-18deg.svg';pat.write_text(pattern)
cutpaths=[];cutfiles=[]
for name,w,h in [('band',240,96),('slim',64,144),('divider',480,64),('corner',96,96)]:
    shift=h*math.tan(angle);d=f'M{shift:.9f} 0H{w}L{w-shift:.9f} {h}H0Z'
    if name=='corner':d=f'M{shift:.9f} 0H{w}V16H{16+(h-16)*math.tan(angle):.9f}L16 {h}H0Z'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" fill="currentColor"><path d="{d}"/></svg>'
    p=A/f'graphics/patterns/sportzz-graphic-signal-cut-{name}-18deg.svg';p.write_text(svg);cutfiles.append(rel(p))
    cutpaths.append(f'<g id="{name}" transform="translate({len(cutpaths)*540} 0)"><path d="{d}"/></g>')
cuts=A/'graphics/patterns/sportzz-graphic-signal-cuts.svg';cuts.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2160 144" fill="currentColor">'+''.join(cutpaths)+'</svg>')
for id,p,desc,usage in [('GRAPHIC-01',pat,'Patrón modular de líneas a 18° respecto a la vertical',['repeatable-background']),('GRAPHIC-02',cuts,'Cuatro formas de corte direccional a 18°',['section-divider','hero-accent'])]:
    assets.append({'id':id,'name':p.name,'path':rel(p),'category':'graphics','description':desc,'prompt':GRAPHIC_REFERENCE_PROMPT,'resolution':'scalable','format':'svg','ratio':'tile' if id=='GRAPHIC-01' else '15:1','usage':usage,'alt':'' ,'notes':'Precisely reconstructed mathematical paths following Magnific vector reference, not raw model geometry. No gradients, filters or embedded raster. Angle measured from vertical.','review_status':'internally_reviewed','status':['vectorized','exported','validated'],'source':{'generator':'Local mathematical SVG reconstruction from Magnific / Recraft v4 Pro Vector reference','reference':'sources/magnific-references/sportzz-reference-graphic-directions.svg'},'components':cutfiles if id=='GRAPHIC-02' else []})

# Motion reference angles were approximate; final art is an exact-18-degree reconstruction.
dx=1350*math.tan(angle);pieces=['<path d="M0 0H2400V1350H0Z" fill="#080B09"/>']
for x,width,col in [(160,210,'#111613'),(500,60,'#171D19'),(2210,170,'#171D19'),(2370,20,'#171D19')]:
    pieces.append(f'<path d="M{x} 0h{width}l{-dx:.9f} 1350h{-width}Z" fill="{col}"/>')
for x,y,length in [(310,0,300),(2170,980,370)]:
    sh=length*math.tan(angle);pieces.append(f'<path d="M{x} {y}h5l{-sh:.9f} {length}h-5Z" fill="#B6FF00"/>')
motion='<svg xmlns="http://www.w3.org/2000/svg" width="2400" height="1350" viewBox="0 0 2400 1350">'+''.join(pieces)+'</svg>'
mot=A/'graphics/backgrounds/sportzz-graphic-motion-background-18deg.svg';mot.write_text(motion)
mp=mot.with_name('sportzz-graphic-motion-background-16x9-reconstructed-master.png');cairosvg.svg2png(bytestring=motion.encode(),write_to=str(mp))
web=mp.with_name('sportzz-graphic-motion-background-16x9.webp');export(Image.open(mp),web,(2048,1152))
raw=A/'graphics/backgrounds/sportzz-graphic-motion-background-16x9-master.png'
assets.append({'id':'GRAPHIC-05','name':web.name,'path':rel(web),'category':'graphics','description':'Fondo de movimiento geométrico a 18°','prompt':GRAPHIC[2][-1],'resolution':[2048,1152],'format':'webp','ratio':'16:9','usage':['hero-background','section-background'],'alt':'Bandas diagonales discretas sobre negro con dos acentos verdes.','notes':'Magnific original retained as reference only: its diagonals were approximate. Final vector reconstruction enforces 18 degrees from vertical and quiet center; no gradient or glow.','review_status':'internally_reviewed','status':['generated','vectorized','exported','optimized','validated'],'master':{'path':rel(mp),'resolution':[2400,1350],'format':'png','unchanged':False},'editable_vector':rel(mot),'generated_reference':rel(raw),'source':{'generator':'Magnific direction + local exact mathematical reconstruction','creation_page':'https://www.magnific.com/app/creation/mE60wGihJQ','requested_resolution':'2k','credits':75}})
runs.extend([{'id':'GRAPHIC-05','prompt':GRAPHIC[2][-1],'status':'reference_only_reconstructed_to_exact_angle','credits':75},{'id':'ICON-REFERENCE','prompt':ICON_REFERENCE_PROMPT,'status':'reference_only_reconstructed_to_UI_spec','credits':375},{'id':'GRAPHIC-REFERENCE','prompt':GRAPHIC_REFERENCE_PROMPT,'status':'reference_only_reconstructed_to_exact_angle','credits':375}])
assets.sort(key=lambda a:({'photography':0,'mockups':1,'graphics':2}.get(a['category'],3),a['id']))

def contact(items,name,cols=4):
    cw,ch=512,320;im=Image.new('RGB',(cw*cols,ch*math.ceil(len(items)/cols)),'#080B09')
    for i,a in enumerate(items):
        img=Image.open(R/a['path']).convert('RGB');img=ImageOps.contain(img,(cw-12,ch-12),Image.Resampling.LANCZOS)
        im.paste(img,(i%cols*cw+(cw-img.width)//2,i//cols*ch+(ch-img.height)//2))
    im.save(P/name,quality=92,method=6)
contact([a for a in assets if a['category']=='photography'],'sportzz-preview-photography-contact-sheet.webp')
contact([a for a in assets if a['category']=='mockups'],'sportzz-preview-mockups-contact-sheet.webp')
# Readable graphic overview, generated locally; not a runtime background.
g=Image.new('RGB',(1600,760),'#080B09');dr=ImageDraw.Draw(g)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',15)
for i,a in enumerate(a for a in assets if a['category']=='graphics'):
    x=(i%3)*530;y=(i//3)*380
    dr.rectangle((x+10,y+10,x+520,y+322),fill='#171D19')
    p=R/a['path']
    if p.suffix=='.svg':
        if a['id']=='GRAPHIC-01':
            tile=Image.open(io.BytesIO(cairosvg.svg2png(url=str(p)))).convert('RGBA');base=Image.new('RGBA',(500,300),'#171D19')
            for xx in range(0,500,tile.width):
                for yy in range(0,300,tile.height):base.alpha_composite(tile,(xx,yy))
            im=base
        else:
            im=Image.new('RGBA',(500,300),'#171D19')
            for j,f in enumerate(cutfiles):
                raw=cairosvg.svg2png(bytestring=(R/f).read_text().replace('currentColor','#B6FF00').encode(),output_width=190)
                aimg=Image.open(io.BytesIO(raw));aimg.thumbnail((215,116));im.alpha_composite(aimg,(15+(j%2)*245,20+(j//2)*140))
    else:im=ImageOps.contain(Image.open(p).convert('RGBA'),(500,300),Image.Resampling.LANCZOS)
    im.convert('RGB').save(P/f'sportzz-preview-{a["id"].lower()}.webp',quality=95)
    g.paste(im,(x+15+(500-im.width)//2,y+15+(300-im.height)//2),im if im.mode=='RGBA' else None)
    dr.text((x+18,y+339),a['id']+' / '+a['description'],font=font,fill='#AFB8B0')
g.save(P/'sportzz-preview-graphics-contact-sheet.webp',quality=95)

manifest={'brand':'SPORTZZ','collection':'Visual Asset Library','version':'1.0','date':'2026-11-09','brand_reference':'SPORTZZ Manual de identidad v1.0 / 27.10.2026','generator':'Freepik Magnific + explicitly documented local reconstruction/optimization','counts':{'photography':8,'mockups':8,'graphics_primary':5,'icons':70,'sprite_symbols':70,'required_contact_sheets':4},'credits':{'raster_generations':21,'raster_credits_each':75,'vector_reference_generations':2,'vector_reference_credits_each':375,'total':2325},'assets':assets,'icons_manifest':'assets/icons/icon-manifest.json','sprite':'assets/icons/sprite.svg','pending':['Commercial, likeness and trademark clearance before external commercial use','Final screenshot compositing by development team','Manual display-corner adjustment per chosen device and screenshot aspect ratio'],'status_vocabulary':{'generated':'Magnific returned a result and original file downloaded','vectorized':'Editable vector geometry reconstructed locally; not claimed as untouched model output','exported':'Independent file saved in delivery tree','optimized':'Web derivative encoded and aspect ratio normalized without stretching or upscaling','validated':'Technical checks and internal visual review; not a legal clearance','pending':'Not yet performed'},'licensing':'AI-generated assets: no photographic licenses invented. Commercial suitability and rights checks remain the publisher responsibility.'}
(M/'sportzz-visual-assets.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(M/'sportzz-generation-log.json').write_text(json.dumps({'brand':'SPORTZZ','runs':runs,'model_raster':'Google Nano Banana 2','model_vector_reference':'Recraft v4 Pro Vector via Magnific','raster_resolution_requested':'2k','seed':'not specified','credits_total':sum(r['credits'] for r in runs)},ensure_ascii=False,indent=2))
assert sum(r['credits'] for r in runs)==2325

# Include authentic brand files without altering their geometry.
ref=Path('/srv/opencode-workspace/assets/designer-reference/sportzz-frontend')
brand=R/'assets/brand/sportzz';brand.mkdir(parents=True,exist_ok=True)
for p in (ref/'public/brand/sportzz').glob('*.svg'):shutil.copy2(p,brand/p.name)
fonts=R/'assets/brand/fonts';fonts.mkdir(exist_ok=True)
for p in (ref/'public/fonts/sportzz').glob('*.ttf'):shutil.copy2(p,fonts/p.name)
if (ref/'public/fonts/sportzz/licenses').exists():
    shutil.copytree(ref/'public/fonts/sportzz/licenses',fonts/'licenses',dirs_exist_ok=True)

# Static, self-contained catalog; no CDN or build tool required.
def cards(category):
    result=[]
    for a in assets:
        if a['category']!=category:continue
        path=a['path'];is_svg=path.endswith('.svg')
        preview=f'assets/magnific/previews/sportzz-preview-{a["id"].lower()}.webp' if is_svg else path
        result.append(f'<article><a href="{path}"><img src="{preview}" alt="{html.escape(a["alt"] or a["description"])}" loading="lazy" width="640" height="360"></a><div><span class="eyebrow">{a["id"]}</span><h3>{html.escape(a["description"])}</h3><p class="filename">{a["name"]}</p><p>{html.escape(a["notes"])}</p><a href="{path}" download>Descargar recurso ↗</a></div></article>')
    return ''.join(result)
icons=json.loads((R/'assets/icons/icon-manifest.json').read_text())['icons']
iconcards=''.join(f'<div class="icon" data-name="{e["id"]}"><svg width="24" height="24" aria-hidden="true"><use href="assets/icons/sprite.svg#{e["id"]}"/></svg><span>{e["id"]}</span></div>' for e in icons)
content=f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SPORTZZ / Visual Asset Library 1.0</title><link rel="icon" href="assets/brand/sportzz/isotipo-verde.svg"><style>
@font-face{{font-family:Barlow;src:url(assets/brand/fonts/BarlowCondensed-Bold.ttf)}}@font-face{{font-family:Inter;src:url(assets/brand/fonts/Inter-Variable.ttf)}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#080B09;color:#F5F7F3;font-family:Inter,sans-serif}}a{{color:inherit;text-underline-offset:4px}}a:focus-visible,input:focus-visible,button:focus-visible{{outline:2px solid #B6FF00;outline-offset:5px}}header{{padding:26px 5%;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #38433B;gap:20px}}header img{{width:140px;height:auto}}nav{{display:flex;gap:24px;flex-wrap:wrap;font-size:13px}}.hero{{min-height:570px;background:linear-gradient(90deg,rgba(8,11,9,.93),rgba(8,11,9,.05)),url(assets/magnific/photography/hero/sportzz-photo-hero-athletics-16x9.webp) center/cover;display:flex;align-items:center;padding:60px 5%}}.eyebrow{{color:#B6FF00;font-size:11px;letter-spacing:.13em;font-weight:600}}h1{{font-family:Barlow,sans-serif;font-size:92px;line-height:.95;margin:22px 0}}h1 em{{font-style:normal;color:#B6FF00}}.lead{{max-width:470px;font-size:16px;line-height:1.7;color:#C8D0C8}}.stats{{display:flex;gap:30px;flex-wrap:wrap;margin-top:28px;font-size:13px}}.stats b{{display:block;font-family:Barlow;font-size:30px;color:#B6FF00}}main{{padding:30px 5% 80px}}section{{padding:55px 0;border-bottom:1px solid #38433B;scroll-margin-top:20px}}h2{{font-family:Barlow;font-size:48px;line-height:1.05;margin:8px 0 16px}}section>p{{max-width:760px;color:#AFB8B0;line-height:1.7}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px;margin-top:30px}}article{{background:#171D19;border-radius:8px;overflow:hidden}}article img{{display:block;width:100%;height:220px;object-fit:contain;background:#101511}}article>div{{padding:20px}}h3{{font-size:18px;margin:10px 0}}article p{{font-size:12px;color:#AFB8B0;line-height:1.6}}.filename{{overflow-wrap:anywhere;font-family:monospace}}article a[download]{{font-size:12px}}.toolbar{{display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin:28px 0}}input,button{{font:inherit;color:inherit;border:1px solid #536357;background:#171D19;border-radius:6px;min-height:44px;padding:10px 16px}}input{{min-width:260px}}button{{cursor:pointer}}.icongrid{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:1px;background:#38433B;border:1px solid #38433B}}.icon{{display:flex;align-items:center;justify-content:center;gap:16px;flex-direction:column;min-height:110px;background:#080B09;padding:14px 5px;color:#F5F7F3}}.icon span{{font-size:10px;overflow-wrap:anywhere}}.icongrid.light .icon{{background:#F5F7F3;color:#080B09}}.notice{{border-left:3px solid #B6FF00;padding:8px 0 8px 20px;color:#AFB8B0;line-height:1.7;font-size:13px}}footer{{padding:30px 5%;color:#AFB8B0;font-size:12px}}.review{{display:flex;gap:20px;flex-wrap:wrap}}[hidden]{{display:none!important}}@media(max-width:800px){{header{{align-items:flex-start;flex-direction:column}}nav{{gap:14px}}.hero{{min-height:540px;background-position:65% center;padding:36px 5%}}h1{{font-size:66px}}.lead{{font-size:14px;max-width:315px}}.grid{{grid-template-columns:1fr}}h2{{font-size:38px}}.icongrid{{grid-template-columns:repeat(3,minmax(0,1fr))}}article img{{height:auto;aspect-ratio:16/9}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head><body><header><img src="assets/brand/sportzz/logotipo-blanco.svg" alt="SPORTZZ"><nav aria-label="Catálogo"><a href="#photography">Fotografía</a><a href="#mockups">Mockups</a><a href="#graphics">Gráficos</a><a href="#icons">Iconos</a><a href="#delivery">Entrega</a></nav></header><div class="hero"><div><span class="eyebrow">VISUAL ASSET LIBRARY / COLLECTION 1.0</span><h1>EL DEPORTE.<br><em>SIN PAUSA.</em></h1><p class="lead">Una biblioteca visual para construir SPORTZZ. Fotografía editorial, superficies listas para componer y una familia de iconos propia.</p><div class="stats"><span><b>08</b>Fotografías</span><span><b>08</b>Mockups</span><span><b>05</b>Gráficos</span><span><b>70</b>Iconos SVG</span></div></div></div><main>
<section id="photography"><span class="eyebrow">01 / PHOTOGRAPHY SYSTEM</span><h2>Acción realista. Emoción cercana.</h2><p>Escenas ficticias generadas por IA; no representan acontecimientos deportivos reales. Ocho originales independientes, un hero a 2400 × 1350 y fotografías web a 2048 × 1152.</p><div class="grid">{cards('photography')}</div></section>
<section id="mockups"><span class="eyebrow">02 / MOCKUP SYSTEM</span><h2>El contenido lo pones tú.</h2><p>Pantallas y áreas de marca vacías para insertar capturas reales y los SVG auténticos. Sin interfaces inventadas. Ajustar esquinas y recorte a cada pantalla antes de componer.</p><div class="grid">{cards('mockups')}</div></section>
<section id="graphics"><span class="eyebrow">03 / GRAPHIC ASSETS</span><h2>18° que marcan el ritmo.</h2><p>Geometrías reconstruidas matemáticamente a 18° respecto a la vertical. Textura modular de bordes verificados y fondos de contraste bajo. Las referencias de Magnific se conservan por separado.</p><div class="grid">{cards('graphics')}</div></section>
<section id="icons"><span class="eyebrow">04 / SPORTZZ SIGNAL ICONS</span><h2>Setenta signos. Un sistema.</h2><p>SVG vectoriales independientes: viewBox 24 × 24, trazo 1,75 px, currentColor y terminaciones redondeadas. Reconstrucción original a partir de una referencia de Magnific; no son setenta salidas nativas del modelo.</p><div class="toolbar"><label for="search">Buscar icono</label><input id="search" type="search" placeholder="home, play, football…"><button id="theme" type="button" aria-pressed="false">Cambiar fondo de iconos</button><label for="size">Tamaño</label><select id="size"><option>16</option><option>20</option><option selected>24</option><option>32</option></select></div><p id="count" aria-live="polite">70 iconos</p><div class="icongrid" id="icongrid">{iconcards}</div></section>
<section id="delivery"><span class="eyebrow">05 / HANDOFF</span><h2>Listo para desarrollar.</h2><div class="review"><a href="assets/magnific/manifests/sportzz-visual-assets.json">Manifiesto visual</a><a href="assets/icons/icon-manifest.json">Manifiesto de iconos</a><a href="assets/icons/sprite.svg">Sprite SVG</a><a href="ASSET-README.md">Guía de uso</a><a href="assets/magnific/previews/sportzz-preview-photography-contact-sheet.webp">Hoja de fotografía</a><a href="assets/magnific/previews/sportzz-preview-mockups-contact-sheet.webp">Hoja de mockups</a><a href="assets/magnific/previews/sportzz-preview-icons-contact-sheet.webp">Hoja de iconos</a><a href="assets/magnific/previews/sportzz-preview-graphics-contact-sheet.webp">Catálogo gráfico</a></div><p class="notice">Revisión técnica e interna, no autorización comercial. Comprobar derechos, posibles semejanzas y contexto antes de publicar. La integración con capturas reales queda pendiente. No utilizar las hojas de contacto como assets de interfaz.</p></section></main><footer>SPORTZZ / VISUAL ASSETS — COLLECTION 1.0 · 09.11.2026 · Imágenes: Magnific / Nano Banana 2 · Vectorización y exportación documentadas.</footer><script>
const grid=document.querySelector('#icongrid');const items=[...grid.children];document.querySelector('#search').addEventListener('input',e=>{{const q=e.target.value.toLowerCase().trim();let count=0;items.forEach(el=>{{el.hidden=!el.dataset.name.includes(q);if(!el.hidden)count++}});document.querySelector('#count').textContent=count+' iconos'}});document.querySelector('#theme').addEventListener('click',e=>{{const light=grid.classList.toggle('light');e.target.setAttribute('aria-pressed',String(light))}});document.querySelector('#size').addEventListener('change',e=>{{grid.querySelectorAll('svg').forEach(el=>{{el.setAttribute('width',e.target.value);el.setAttribute('height',e.target.value)}})}});
</script></body></html>'''
content=content.replace('input,button{','input,button,select{').replace('button:focus-visible{','button:focus-visible,select:focus-visible{')
content=content.replace('@media(max-width:800px){','@media(max-width:800px){.hero .eyebrow{display:block;max-width:240px;line-height:1.7}')
(R/'index.html').write_text(content)
print('21 primary assets exported; responsive derivatives, manifests and catalog built.')
