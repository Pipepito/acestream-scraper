"""SPORTZZ SIGNAL ICONS: original normalized geometric reconstruction.
Magnific reference is retained separately; final UI paths are authored here.
No external icon library or copied path data is used.
"""
from pathlib import Path
import math, json, hashlib, sys, io
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
import cairosvg
R=Path(__file__).resolve().parents[2]
OUT=R/'assets/icons';PRE=R/'assets/magnific/previews'
PRE.mkdir(parents=True,exist_ok=True)
def circle(x=12,y=12,r=9):return f'M{x-r:g} {y:g}a{r:g} {r:g} 0 1 0 {2*r:g} 0a{r:g} {r:g} 0 1 0 {-2*r:g} 0'
def box(x,y,w,h,r=1.5):return f'M{x+r} {y}H{x+w-r}Q{x+w} {y} {x+w} {y+r}V{y+h-r}Q{x+w} {y+h} {x+w-r} {y+h}H{x+r}Q{x} {y+h} {x} {y+h-r}V{y+r}Q{x} {y} {x+r} {y}Z'
def poly(points,close=True):return 'M'+'L'.join(f'{x:.3f} {y:.3f}' for x,y in points)+('Z' if close else '')
gear=[]
for tooth in range(8):
    for delta,rad in [(-.5,7.2),(-.28,7.2),(-.23,9),(.23,9),(.28,7.2),(.5,7.2)]:
        a=(tooth+delta)*math.pi/4;gear.append((12+rad*math.cos(a),12+rad*math.sin(a)))
G={}
G['navigation']={
 'home':'M3.5 10.5L12 3.5l8.5 7V19a1.5 1.5 0 0 1-1.5 1.5H15v-6H9v6H5A1.5 1.5 0 0 1 3.5 19Z',
 'menu':'M4 6.5h16M4 12h16M4 17.5h16',
 'arrow-left':'M20 12H4m6-6-6 6 6 6',
 'arrow-right':'M4 12h16m-6-6 6 6-6 6',
 'arrow-up':'M12 20V4m-6 6 6-6 6 6',
 'arrow-down':'M12 4v16m-6-6 6 6 6-6',
 'chevron-left':'M15 5.5 8.5 12 15 18.5',
 'chevron-right':'M9 5.5 15.5 12 9 18.5',
 'chevron-up':'M5.5 15 12 8.5 18.5 15',
 'chevron-down':'M5.5 9 12 15.5 18.5 9',
 'close':'M5.5 5.5l13 13m0-13-13 13',
 'external-link':'M13.5 4H20v6.5M20 4l-9.5 9.5M9 4H5.5A1.5 1.5 0 0 0 4 5.5v13A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15',
 'breadcrumb':'M3.5 11.5h4v4h-4ZM11.5 8.5 15 12l-3.5 3.5M18 8.5l3.5 3.5-3.5 3.5',
}
G['actions']={
 'plus':'M12 4v16M4 12h16', 'minus':'M4 12h16',
 'edit':'M4 15.5 15.5 4a2.12 2.12 0 0 1 3 0l1.5 1.5a2.12 2.12 0 0 1 0 3L8.5 20H4v-4.5ZM13.5 6l4.5 4.5',
 'trash':'M3.5 6.5h17M9 6.5V4h6v2.5M5.5 6.5l1 12a2 2 0 0 0 2 2h7a2 2 0 0 0 2-2l1-12M10 10v7m4-7v7',
 'save':box(4,3.5,16,17,1)+'M8 3.5v6h8v-6M8 20.5v-6h8v6',
 'copy':box(8,7.5,12,13)+'M15.5 7.5v-4H4v13h4',
 'download':'M12 3v12m-4-4 4 4 4-4M4 15.5v5h16v-5',
 'upload':'M12 15V3m-4 4 4-4 4 4M4 15.5v5h16v-5',
 'refresh':'M20 4.5v5h-5M4 19.5v-5h5M19.5 9a8 8 0 0 0-13.8-3.4M4.5 15a8 8 0 0 0 13.8 3.4',
 'search':circle(10.5,10.5,6.5)+'M15.2 15.2 21 21',
 'filter':'M3.5 4.5h17L14 12v6l-4 2v-8Z',
 'sort-ascending':'M6 20V4m-3 3 3-3 3 3M12 6h8m-8 6h5m-5 6h2',
 'sort-descending':'M6 4v16m-3-3 3 3 3-3M12 6h2m-2 6h5m-5 6h8',
 'more-horizontal':circle(5,12,1)+circle(12,12,1)+circle(19,12,1),
 'settings':poly(gear)+circle(12,12,3),
 'share':circle(5,12,2.5)+circle(18,5,2.5)+circle(18,19,2.5)+'M7.2 10.8l8.6-4.6M7.2 13.2l8.6 4.6',
 'link':'M9.5 14.5l5-5M8.5 15l-1 1a2.83 2.83 0 0 1-4-4l4-4a2.83 2.83 0 0 1 4 0M12.5 16a2.83 2.83 0 0 0 4 0l4-4a2.83 2.83 0 0 0-4-4l-1 1',
 'eye':'M2.5 12Q12 0 21.5 12Q12 24 2.5 12Z'+circle(12,12,3),
 'eye-off':'M3 3l18 18M8 5.9Q15 3.5 21.5 12q-1.8 2.5-4.1 4.3M14.5 18.4Q7.5 20.3 2.5 12q1.6-2.2 3.6-3.8M9.9 9.9a3 3 0 0 0 4.2 4.2',
}
G['status']={
 'check':'M4 12.5 9.5 18 20 6.5',
 'check-circle':circle()+'M7.5 12l3 3 6-6',
 'alert-triangle':'M10.5 4.3a1.73 1.73 0 0 1 3 0l8 13.8a1.73 1.73 0 0 1-1.5 2.6H4a1.73 1.73 0 0 1-1.5-2.6ZM12 8.5v5M12 17v.2',
 'alert-circle':circle()+'M12 7.5v6M12 17v.2',
 'info':circle()+'M12 7v.2M10.5 11H12v6h1.5',
 'help-circle':circle()+'M9.3 9a2.8 2.8 0 1 1 4.3 2.4c-1.3.7-1.6 1.1-1.6 2.6M12 17v.2',
 'clock':circle()+'M12 6.5v6l4 2',
 'loader':'M12 3a9 9 0 1 1-9 9M3.5 8.8l.1-.2M5.3 5.9l.1-.1M8.5 3.7l.1-.1',
 'x-circle':circle()+'M8.5 8.5l7 7m0-7-7 7',
 'pause-circle':circle()+'M9.5 8.5v7m5-7v7',
}
G['data']={
 'database':'M4 6c0-4 16-4 16 0s-16 4-16 0Zm0 0v12c0 4 16 4 16 0V6M4 12c0 4 16 4 16 0',
 'server':box(3.5,3.5,17,7)+box(3.5,13.5,17,7)+'M7 7h.2M7 17h.2M15 7h2M15 17h2',
 'network':box(8.5,3,7,5)+box(2.5,16,7,5)+box(14.5,16,7,5)+'M12 8v4M6 16v-4h12v4',
 'terminal':box(3,4.5,18,15)+'M6.5 9l3 3-3 3M12.5 15h5',
 'file':'M5 3.5h9l5 5v12H5ZM14 3.5v5h5',
 'file-text':'M5 3.5h9l5 5v12H5ZM14 3.5v5h5M8.5 12h7M8.5 16h5',
 'code':'M7.5 6 2.5 12l5 6M16.5 6l5 6-5 6M14 3.5l-4 17',
 'layers':'M12 3 2.5 8 12 13l9.5-5ZM2.5 12l9.5 5 9.5-5M2.5 16l9.5 5 9.5-5',
 'activity':'M2.5 12h5L10 5l4 14 2.5-7h5',
 'chart-line':'M3.5 3.5v17h17M7 15l4-5 4 2 5-7',
 'chart-bar':'M3.5 3.5v17h17M7 16.5v-4m5 4v-9m5 9v-6',
 'list':'M8 6h12M8 12h12M8 18h12M3.5 6h.2M3.5 12h.2M3.5 18h.2',
 'grid':box(3.5,3.5,6.5,6.5,1)+box(14,3.5,6.5,6.5,1)+box(3.5,14,6.5,6.5,1)+box(14,14,6.5,6.5,1),
 'table':box(3,4,18,16)+'M3 9h18M3 14.5h18M9 9v11M15 9v11',
 'calendar':box(3.5,5,17,15.5)+'M7.5 3v4M16.5 3v4M3.5 10h17M7.5 14h2M14.5 14h2M7.5 17.5h2',
 'history':'M3 4v5h5M3.6 8.7a8.5 8.5 0 1 1 .4 7.2M12 7v5.5l4 2',
}
G['media']={
 'play':'M7 3.5 21 12 7 20.5Z',
 'pause':'M7 4.5v15M17 4.5v15',
 'stop':box(4.5,4.5,15,15,1.5),
 'volume':'M3 9h4l5-4v14l-5-4H3ZM15.5 8a5.7 5.7 0 0 1 0 8M18.5 5a10 10 0 0 1 0 14',
 'volume-off':'M3 9h4l5-4v14l-5-4H3ZM16 8l5 8m0-8-5 8',
 'fullscreen':'M9 3.5H3.5V9M15 3.5h5.5V9M3.5 15v5.5H9M20.5 15v5.5H15',
 'trophy':'M7 3.5h10v6a5 5 0 0 1-10 0ZM7 5H3v2a4 4 0 0 0 4 4m10-6h4v2a4 4 0 0 1-4 4M12 14.5v6M8 20.5h8',
 'football':circle()+'M12 7.5 16.3 10.6 14.7 15.7H9.3L7.7 10.6ZM12 7.5V3M16.3 10.6l4.3-1.3M14.7 15.7l2.8 3.4M9.3 15.7l-2.8 3.4M7.7 10.6 3.4 9.3',
 'basketball':circle()+'M3 12h18M12 3v18M6 5.3c6 2.7 6 10.7 0 13.4M18 5.3c-6 2.7-6 10.7 0 13.4',
 'tennis':circle()+'M5.7 5.6C12 7.5 12 16.5 5.7 18.4M18.3 5.6C12 7.5 12 16.5 18.3 18.4',
 'racing-flag':'M4 21V3.5c5-3 9 3 16 0v11c-7 3-11-3-16 0M9.3 3.1v11M14.7 4.5v11M4 9c5-3 9 3 16 0',
 'whistle':'M20.5 5.5h-9V9H8a5.5 5.5 0 1 0 5.5 5.5V12l7-3Z'+circle(8,14.5,2)+'M4 5 2.5 3.5M7 4V2.5',
}
SAMPLE={'home','search','settings','activity','football'}
only='--sample' in sys.argv
entries=[];symbols=[];rendered=[]
for fam,items in G.items():
    (OUT/fam).mkdir(parents=True,exist_ok=True)
    for name,d in items.items():
        if only and name not in SAMPLE:continue
        filename=f'sportzz-icon-{fam}-{name}-24.svg'
        attrs='fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
        svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" {attrs}><path d="{d}"/></svg>\n'
        (OUT/fam/filename).write_text(svg)
        symbols.append(f'<symbol id="{name}" viewBox="0 0 24 24" {attrs}><path d="{d}"/></symbol>')
        entries.append({'id':name,'name':name,'family':fam,'filename':filename,'path':f'assets/icons/{fam}/{filename}','viewBox':'0 0 24 24','stroke':1.75,'tags':[fam,*name.split('-')],'provenance':'Original geometric reconstruction following Magnific reference and SPORTZZ specifications; no third-party icon paths imported','status':['vectorized','exported','validated'],'validation':{'xml':True,'currentColor':True,'no_raster':True,'sizes':[16,20,24,32]}})
        # All four sizes rasterized; verify no stroke clips the viewBox boundary.
        for size in [16,20,24,32]:
            png=cairosvg.svg2png(bytestring=svg.replace('currentColor','#F5F7F3').encode(),output_width=size*4,output_height=size*4)
            im=Image.open(io.BytesIO(png));bb=im.getbbox();assert bb and bb[0]>0 and bb[1]>0 and bb[2]<size*4 and bb[3]<size*4,(name,size,bb)
        rendered.append((fam,name,svg))
def sheet(data,path,cols=10,cellw=160,cellh=112):
    rows=math.ceil(len(data)/cols);im=Image.new('RGB',(cols*cellw,rows*cellh),'#080B09');draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
    for i,(fam,name,svg) in enumerate(data):
        x=(i%cols)*cellw;y=(i//cols)*cellh
        raw=cairosvg.svg2png(bytestring=svg.replace('currentColor','#F5F7F3').encode(),output_width=40,output_height=40)
        icon=Image.open(io.BytesIO(raw));im.paste(icon,(x+(cellw-40)//2,y+19),icon)
        draw.text((x+cellw/2,y+74),name,font=font,anchor='mt',fill='#AFB8B0')
    im.save(path,quality=95)
sheet(rendered,PRE/('sportzz-preview-icons-sample-5.webp' if only else 'sportzz-preview-icons-contact-sheet.webp'),cols=5 if only else 10)
if not only:
    assert len(entries)==70
    assert len({hashlib.sha256(G[e['family']][e['id']].encode()).hexdigest() for e in entries})==70
    (OUT/'sprite.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg">'+''.join(symbols)+'</svg>\n')
    root=ET.parse(OUT/'sprite.svg').getroot();assert len({e.attrib['id'] for e in root})==70
    (OUT/'icon-manifest.json').write_text(json.dumps({'brand':'SPORTZZ','collection':'SPORTZZ SIGNAL ICONS','version':'1.0','count':70,'reference':'sources/magnific-references/sportzz-reference-signal-icons-sample-5.svg','icons':entries},indent=2))
    # Final overview is explicitly separated by family; labels are typeset locally.
    heights=[40+math.ceil(len(items)/10)*112 for items in G.values()]
    grouped=Image.new('RGB',(1600,sum(heights)),'#080B09');gd=ImageDraw.Draw(grouped)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    y=0
    for fam,hh in zip(G,heights):
        gd.text((20,y+12),fam.upper(),font=font,fill='#B6FF00')
        data=[item for item in rendered if item[0]==fam]
        temp=PRE/f'sportzz-preview-icons-{fam}.webp';sheet(data,temp)
        grouped.paste(Image.open(temp),(0,y+40));y+=hh
    grouped.save(PRE/'sportzz-preview-icons-contact-sheet.webp',quality=95)
    # Scale review: all icons at 16/20/24/32 px on light/dark panels.
    im=Image.new('RGB',(1440,70*56+72),'#080B09');dr=ImageDraw.Draw(im)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    dr.text((24,22),'SPORTZZ SIGNAL ICONS / 16, 20, 24, 32 px / DARK + LIGHT',font=font,fill='#B6FF00')
    dr.rectangle((720,72,1440,im.height),fill='#F5F7F3')
    for i,(fam,name,svg) in enumerate(rendered):
        y=72+i*56;dr.text((20,y+19),name,font=font,fill='#AFB8B0')
        for theme,col,offset in [('dark','#F5F7F3',230),('light','#080B09',830)]:
            for j,size in enumerate([16,20,24,32]):
                raw=cairosvg.svg2png(bytestring=svg.replace('currentColor',col).encode(),output_width=size*2,output_height=size*2)
                icon=Image.open(io.BytesIO(raw)).resize((size,size),Image.Resampling.LANCZOS)
                im.paste(icon,(offset+j*125,y+(56-size)//2),icon)
    im.save(PRE/'sportzz-preview-icons-size-review.webp',quality=95)
print('Sample exported' if only else '70 SVGs + sprite validated and rendered at four sizes.')
