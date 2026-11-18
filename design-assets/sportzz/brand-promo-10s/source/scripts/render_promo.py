"""SPORTZZ 10-second brand promo. True vector branding, authored type and UI.
No paid generation in this script. All exports have 240 frames at 24 fps.
"""
from pathlib import Path
import io, json, math, wave, shutil, subprocess, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
import cv2, cairosvg
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

R=Path(__file__).resolve().parents[2];S=R/'source';WORK=R/'work';PRE=R/'previews'
W,H,FPS,N=1280,720,24,240
FF='/usr/bin/ffmpeg';FP='/usr/bin/ffprobe'
BG=(8,11,9);FG=(245,247,243);GREEN=(182,255,0);CHARCOAL=(23,29,25)
REF=Path('/srv/opencode-workspace/assets/designer-reference/sportzz-frontend')
LIB=Path('/srv/opencode-workspace/assets/sportzz/visual-assets-collection-1-20261109/assets/magnific/photography/sports')
for p in [WORK,PRE,S/'brand',S/'fonts',S/'audio',S/'video']:p.mkdir(parents=True,exist_ok=True)
for name in ['logotipo-blanco.svg','isotipo-verde.svg']:
    if (REF/'public/brand/sportzz'/name).exists():shutil.copy2(REF/'public/brand/sportzz'/name,S/'brand'/name)
for name in ['BarlowCondensed-Bold.ttf','Inter-Variable.ttf']:
    if (REF/'public/fonts/sportzz'/name).exists():shutil.copy2(REF/'public/fonts/sportzz'/name,S/'fonts'/name)
if (REF/'public/fonts/sportzz/licenses').exists():shutil.copytree(REF/'public/fonts/sportzz/licenses',S/'fonts/licenses',dirs_exist_ok=True)
for weight,label in [(400,'Regular'),(600,'SemiBold')]:
    dest=S/f'fonts/Inter-{label}.ttf'
    if not dest.exists():instantiateVariableFont(TTFont(S/'fonts/Inter-Variable.ttf'),{'wght':weight},inplace=False).save(dest)
def font(size,kind='display'):
    return ImageFont.truetype(str(S/'fonts'/({'display':'BarlowCondensed-Bold.ttf','body':'Inter-Regular.ttf','medium':'Inter-SemiBold.ttf'}[kind])),size)
def run(args):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[-5000:])
    return r.stdout
def probe(p):return json.loads(run([FP,'-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def svg_img(name,width):
    raw=cairosvg.svg2png(url=str(S/'brand'/name),output_width=width)
    im=Image.open(io.BytesIO(raw)).convert('RGBA');bb=im.getbbox()
    return im.crop(bb)
logo=svg_img('logotipo-blanco.svg',500);iso=svg_img('isotipo-verde.svg',110)
def smooth(x):x=max(0.,min(1.,x));return x*x*(3-2*x)
def ramp(t,start,end,fade=.13):return smooth((t-start)/fade)*smooth((end-t)/fade)
def paste_alpha(base,over,xy,opacity=1):
    if opacity<=0:return
    over=over.copy()
    if opacity<1:over.putalpha(over.getchannel('A').point(lambda v:round(v*opacity)))
    base.alpha_composite(over,(round(xy[0]),round(xy[1])))
def title_layer(texts,xy,size):
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im);x,y=xy;f=font(size)
    for s,col in texts:d.text((x,y),s,font=f,fill=col);x+=d.textlength(s,font=f)
    return im
title1=title_layer([('EL DEPORTE.',FG)],(64,516),86)
title2=title_layer([('SIN ',FG),('PAUSA.',GREEN)],(64,516),86)
experience=Image.new('RGBA',(W,H));de=ImageDraw.Draw(experience)
de.text((65,257),'Explora.',font=font(53),fill=FG)
de.text((65,315),'Descubre.',font=font(53),fill=FG)
de.text((65,383),'Vive el directo.',font=font(35),fill=GREEN)
de.line((66,446,187,446),fill=GREEN,width=3)
def center_text(draw,s,y,f,col):draw.text(((W-draw.textlength(s,font=f))/2,y),s,font=f,fill=col)
end_type=Image.new('RGBA',(W,H));ed=ImageDraw.Draw(end_type)
center_text(ed,'EL DEPORTE. SIN PAUSA.',391,font(48),FG)
center_text(ed,'Una nueva forma de descubrir el deporte en streaming.',473,font(20,'body'),FG)

# UI is an authored concept, not AI-generated lettering or a fabricated schedule.
ui=Image.new('RGB',(1280,720),BG);du=ImageDraw.Draw(ui)
ui.paste(Image.new('RGB',(1280,88),CHARCOAL),(0,0))
mark=svg_img('logotipo-blanco.svg',179);ui.paste(mark,(43,25),mark)
for x,s in [(280,'Deportes'),(463,'Programación'),(702,'Directos')]:du.text((x,35),s,font=font(20,'medium'),fill=GREEN if x==280 else FG)
du.text((44,127),'DESCUBRE TU PRÓXIMO DEPORTE',font=font(43),fill=FG)
du.text((44,187),'Explora disciplinas y consulta la programación.',font=font(20,'body'),fill=(175,184,176))
for i,(slug,title) in enumerate([('football','Fútbol'),('basketball','Baloncesto'),('tennis','Tenis')]):
    dest=S/'video'/f'sportzz-ui-category-{slug}.webp'
    if not dest.exists():shutil.copy2(LIB/f'sportzz-photo-{slug}-action-16x9.webp',dest)
    photo=ImageOps.fit(Image.open(dest).convert('RGB'),(380,234),Image.Resampling.LANCZOS)
    x=44+i*406;ui.paste(photo,(x,255));du.rounded_rectangle((x,489,x+380,559),radius=8,fill=CHARCOAL)
    du.text((x+20,507),title,font=font(25,'medium'),fill=FG)
du.rounded_rectangle((44,603,321,666),radius=8,fill=GREEN)
du.text((67,622),'Ver programación',font=font(22,'medium'),fill=BG)
du.text((790,630),'INTERFAZ CONCEPTUAL',font=font(14,'medium'),fill=(175,184,176))
ui.save(S/'video/sportzz-concept-ui-authored.png')
UI=np.asarray(ui)

raw=S/'video/sportzz-generated-source-preview.mp4';norm=WORK/'sportzz-normalized-24fps.mp4'
picture=S/'video/sportzz-retouched-picture.mp4'
run([FF,'-y','-v','error','-i',str(picture if picture.exists() else raw),'-vf','fps=24,scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1','-an','-frames:v','240','-c:v','libx264','-threads','2','-preset','fast','-crf','12','-pix_fmt','yuv420p',str(norm)])
anchors=json.loads((S/'video/screen-tracking.json').read_text())
def quad_at(t):
    data=anchors['anchors']
    if t<=data[0]['time']:return np.array(data[0]['quad'],np.float32)
    if t>=data[-1]['time']:return np.array(data[-1]['quad'],np.float32)
    for a,b in zip(data,data[1:]):
        if a['time']<=t<=b['time']:
            z=(t-a['time'])/(b['time']-a['time']);return np.array(a['quad'],np.float32)*(1-z)+np.array(b['quad'],np.float32)*z
    raise AssertionError(t)
def apply_ui(im,t):
    if not anchors['start']<=t<anchors['end']:return im
    a=ramp(t,anchors['start'],anchors['end'],.16)
    q=quad_at(t);matrix=cv2.getPerspectiveTransform(np.array([[0,0],[1279,0],[1279,719],[0,719]],np.float32),q)
    warped=cv2.warpPerspective(UI,matrix,(W,H),flags=cv2.INTER_LANCZOS4)
    mask=cv2.warpPerspective(np.full((720,1280),255,np.uint8),matrix,(W,H),flags=cv2.INTER_LINEAR)
    mask=(mask.astype('float32')/255*a)[...,None];arr=np.asarray(im.convert('RGB')).astype('float32')
    arr=arr*(1-mask)+warped.astype('float32')*mask
    return Image.fromarray(np.clip(arr,0,255).astype('uint8')).convert('RGBA')
def outro(t):
    im=Image.new('RGBA',(W,H),BG+(255,));d=ImageDraw.Draw(im)
    # Exact 18 degrees from vertical, not a guessed model angle.
    x=110+40*smooth((t-7)/3);shift=H*math.tan(math.radians(18))
    band=tuple(round(a*.8+b*.2) for a,b in zip(BG,GREEN))+(255,)
    d.polygon([(x+shift,0),(x+shift+12,0),(x+12,H),(x,H)],fill=band)
    paste_alpha(im,iso,((W-iso.width)/2,121),smooth((t-7.12)/.28))
    z=.98+.02*smooth((t-7.62)/.35);lm=logo.resize((round(logo.width*z),round(logo.height*z)),Image.Resampling.LANCZOS)
    paste_alpha(im,lm,((W-lm.width)/2,249),smooth((t-7.52)/.3))
    paste_alpha(im,end_type,(0,0),smooth((t-7.86)/.26))
    return im
def encoder(path,crf):
    return subprocess.Popen([FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','24','-i','pipe:0','-an','-c:v','libx264','-threads','2','-preset','slow','-crf',str(crf),'-vf','scale=out_color_matrix=bt709:out_range=tv,format=yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-color_range','tv','-frames:v','240','-movflags','+faststart',str(path)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
branded=WORK/'sportzz-brand-picture.mp4';clean=R/'sportzz-brand-promo-10s-clean.mp4'
p1=encoder(branded,14);p2=encoder(clean,16);cap=cv2.VideoCapture(str(norm));review=[]
try:
    for n in range(N):
        ok,frame=cap.read();assert ok,n;t=n/FPS
        base=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert('RGBA')
        if t>=7:base=Image.new('RGBA',(W,H),BG+(255,))
        p2.stdin.write(base.convert('RGB').tobytes())
        if t>=7:final=outro(t)
        else:
            final=apply_ui(base,t)
            # A discrete left-side density plate protects text without an artificial glow.
            if t<4:
                shade=Image.new('RGBA',(W,H));ds=ImageDraw.Draw(shade)
                for x in range(650):ds.line((x,430,x,H),fill=BG+(round(115*(1-x/650)),))
                final.alpha_composite(shade)
            if t<2:paste_alpha(final,title1,(0,0),ramp(t,.12,1.96))
            elif t<4:paste_alpha(final,title2,(0,0),ramp(t,2.02,3.96))
            else:paste_alpha(final,experience,(0,0),ramp(t,4.12,6.95,.2))
            if 6.78<=t<7:
                black=Image.new('RGBA',(W,H),BG+(255,));paste_alpha(final,black,(0,0),smooth((t-6.78)/.22))
        p1.stdin.write(final.convert('RGB').tobytes())
        if n in [0,12,26,40,55,70,84,102,119,140,160,174,190,211,228,239]:
            path=PRE/f'sportzz-promo-frame-{n:03}.jpg';final.convert('RGB').save(path,quality=95);review.append((n,path))
        if n==216:final.convert('RGB').save(R/'sportzz-brand-promo-poster.webp',quality=95,method=6)
finally:
    cap.release()
    for p in [p1,p2]:
        if p.stdin:p.stdin.close()
        err=p.stderr.read();code=p.wait()
        if code:raise RuntimeError(err.decode(errors='replace'))

def read_wav(path):
    with wave.open(str(path),'rb') as f:
        assert f.getsampwidth()==2 and f.getframerate()==48000
        return np.frombuffer(f.readframes(f.getnframes()),'<i2').astype('float32').reshape(-1,f.getnchannels())/32768
def write_wav(path,data):
    with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(48000);f.writeframes((np.clip(data,-1,1)*32767).astype('<i2').tobytes())
audio_info=probe(raw);has_audio=any(s['codec_type']=='audio' for s in audio_info['streams'])
native=WORK/'native.wav';voice=WORK/'voice.wav'
if has_audio:
    run([FF,'-y','-v','error','-i',str(raw),'-vn','-af','apad','-t','10','-ar','48000','-ac','2','-c:a','pcm_s16le',str(native)])
else:write_wav(native,np.zeros((480000,2),np.float32))
run([FF,'-y','-v','error','-i',str(S/'audio/sportzz-voiceover-es-original.mp3'),'-af','highpass=f=70','-ar','48000','-ac','2','-c:a','pcm_s16le',str(voice)])
nat=read_wav(native);v=read_wav(voice);count=480000
if len(v)>int(8.8*48000):
    speed=len(v)/(8.8*48000)
    run([FF,'-y','-v','error','-i',str(voice),'-af',f'atempo={speed}','-ar','48000','-c:a','pcm_s16le',str(WORK/'voice-fit.wav')]);v=read_wav(WORK/'voice-fit.wav')
vo=np.zeros((count,2),np.float32);offset=int(.6*48000);vo[offset:offset+min(len(v),count-offset)]=v[:count-offset]
active=np.abs(vo).max(axis=1)>.015
if active.any():vo*=.105/max(.01,float(np.sqrt(np.mean(vo[active]**2))))
nat=nat[:count];nat*=.15/max(.01,float(np.abs(nat).max()))
duck=cv2.blur(active.astype('float32').reshape(-1,1),(1,6001)).reshape(-1)
nat*=((1-.72*duck)[:,None])
score=np.zeros(count,np.float32);rng=np.random.default_rng(20261109)
def hit(start,hz=52,amp=.17,dur=.18):
    idx=int(start*48000);n=min(int(dur*48000),count-idx)
    if n<=0:return
    t=np.arange(n)/48000;env=np.exp(-t/(dur/6));phase=2*np.pi*(hz*t+32*.018*(1-np.exp(-t/.018)))
    score[idx:idx+n]+=amp*np.sin(phase)*env+rng.normal(0,.018,n)*np.exp(-t/.008)
for time in [0,.58,1.34,2,2.67,3.33,4,7.12,7.6,8.78]:hit(time,45 if time<.1 else 58,.22 if time<.1 or time==7.6 else .11,.42 if time<.1 else .16)
# Restrained two-note electronic pulse, no generic orchestral trailer score.
for start,note in [(1.7,110),(2.34,110),(3.0,130.8128),(3.66,110),(4.55,82.4069),(5.9,110),(8.85,82.4069)]:
    idx=int(start*48000);nn=min(14400,count-idx);t=np.arange(nn)/48000;env=np.sin(np.pi*np.minimum(t/.3,1))**2
    score[idx:idx+nn]+=.026*env*(np.sin(2*np.pi*note*t)+.2*np.sin(2*np.pi*2*note*t))
score*=np.minimum(1,(10-np.arange(count)/48000)/.18)
bed=nat+np.column_stack([score,score*.98]);mix=bed+vo
peak=float(np.abs(mix).max())
if peak>.85:mix*=.85/peak
write_wav(S/'audio/sportzz-voiceover-es-timeline.wav',vo)
write_wav(S/'audio/sportzz-music-sfx-timeline.wav',bed)
write_wav(WORK/'mix-pre.wav',mix)
finalmix=S/'audio/sportzz-final-mix.wav'
run([FF,'-y','-v','error','-i',str(WORK/'mix-pre.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','-ac','2','-t','10','-c:a','pcm_s16le',str(finalmix)])
master=R/'sportzz-brand-promo-10s-master.mp4'
run([FF,'-y','-v','error','-i',str(branded),'-i',str(finalmix),'-map','0:v','-map','1:a','-c:v','copy','-c:a','aac','-b:a','256k','-t','10','-movflags','+faststart',str(master)])
run([FF,'-y','-v','error','-i',str(master),'-c:v','libx264','-threads','2','-preset','slow','-crf','22','-c:a','aac','-b:a','160k','-t','10','-movflags','+faststart',str(R/'sportzz-brand-promo-10s-web.mp4')])
run([FF,'-y','-v','error','-i',str(branded),'-c:v','libx264','-threads','2','-preset','slow','-crf','20','-an','-t','10','-movflags','+faststart',str(R/'sportzz-brand-promo-10s-silent.mp4')])
# Silent VP9 WebM avoids Opus preroll extending the advertised container duration.
run([FF,'-y','-v','error','-i',str(branded),'-c:v','libvpx-vp9','-threads','2','-row-mt','1','-crf','30','-b:v','0','-an','-t','10',str(R/'sportzz-brand-promo-10s-web.webm')])
sheet=Image.new('RGB',(1280,4*206),BG);ds=ImageDraw.Draw(sheet)
for i,(n,p) in enumerate(review):
    thumb=Image.open(p).resize((320,180),Image.Resampling.LANCZOS);x=(i%4)*320;y=(i//4)*206;sheet.paste(thumb,(x,y));ds.text((x+10,y+184),f'{n/24:05.2f} s / frame {n}',font=font(13,'body'),fill=FG)
sheet.save(PRE/'sportzz-brand-promo-storyboard.webp',quality=94,method=6)
report={'duration_target_seconds':10,'fps_target':24,'frames_target':240,'resolution':[1280,720],'color':'SDR Rec.709, not an HDR delivery','voice_model':'ElevenLabs v3 via Magnific','voice_catalog':'Emilio Salcedo, Peninsular Spanish','voice_timeline_offset_seconds':.6,'voice_source_duration_seconds':len(v)/48000,'soundtrack':'Native generated audio plus original locally synthesized dry percussion and electronic pulse; ducked beneath voice','outputs':{}}
for p in sorted(R.glob('*.mp4'))+sorted(R.glob('*.webm')):
    pr=probe(p);vs=next(s for s in pr['streams'] if s['codec_type']=='video');seconds=float(pr['format']['duration'])
    assert int(vs['nb_read_frames'])==240,(p,vs)
    assert vs['avg_frame_rate']=='24/1',(p,vs['avg_frame_rate'])
    assert (vs['width'],vs['height'])==(1280,720)
    assert abs(seconds-10)<.001,(p,seconds)
    report['outputs'][p.name]={'duration_seconds':seconds,'frames':240,'fps':'24/1','resolution':[1280,720],'codec':vs['codec_name'],'has_audio':any(s['codec_type']=='audio' for s in pr['streams']),'bytes':p.stat().st_size}
(R/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
