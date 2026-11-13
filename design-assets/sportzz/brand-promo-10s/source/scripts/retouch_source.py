"""Local temporal clean-up of an unwanted AI-generated shoe mark. No model calls."""
from pathlib import Path
import cv2,numpy as np,subprocess,json
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=R/'source/video';P=R/'previews'
cap=cv2.VideoCapture(str(S/'sportzz-generated-source-preview.mp4'));frames=[]
while True:
 ok,fr=cap.read()
 if not ok:break
 frames.append(fr)
cap.release();assert len(frames)>=240
ref=frames[9];mask=np.zeros(ref.shape[:2],np.uint8)
polys=[[[397,261],[516,312],[679,371],[879,416],[997,425],[980,375],[1058,408],[1119,452],[1119,500],[1082,531],[1004,539],[848,507],[675,456],[542,405],[444,335]],[[230,218],[367,207],[418,272],[383,339],[340,391],[230,365]]]
for poly in polys:cv2.fillPoly(mask,[np.array(poly,np.int32)],255)
mask=cv2.dilate(mask,np.ones((13,13),np.uint8))
heel_mask=np.zeros_like(mask);cv2.fillPoly(heel_mask,[np.array(polys[1],np.int32)],255)
Image.fromarray(mask).save(S/'sportzz-shoe-retouch-reference-mask.png')
sift=cv2.SIFT_create(nfeatures=3500,contrastThreshold=.015)
def feature_mask(fr):
 b,g,r=cv2.split(fr);return (((b.astype(float)>65)&(g.astype(float)>75)&(r.astype(float)<g.astype(float)*1.18))).astype(np.uint8)*255
kp,des=sift.detectAndCompute(cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY),feature_mask(ref));bf=cv2.BFMatcher()
records=[];retouched=[]
for idx,fr in enumerate(frames[:240]):
 if idx in [15,16]:
  fr=frames[17].copy();records.append({'frame':idx,'method':'editorial cut to focused eye avoids unstable final shoe geometry'})
 if 3<=idx<=14:
  if idx==9:hom=np.eye(3)
  else:
   kt,dt=sift.detectAndCompute(cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY),feature_mask(fr))
   matches=[] if dt is None else [a for a,b in bf.knnMatch(des,dt,k=2) if a.distance<.73*b.distance]
   if len(matches)>=7:
    src=np.float32([kp[m.queryIdx].pt for m in matches]);dst=np.float32([kt[m.trainIdx].pt for m in matches]);hom,inliers=cv2.findHomography(src,dst,cv2.RANSAC,4)
   else:hom=None
  if hom is not None:
   region=cv2.warpPerspective(mask,hom,(1280,720));region=(region>15).astype('uint8')*255
   gray=cv2.cvtColor(fr,cv2.COLOR_BGR2GRAY)
   heel=cv2.warpPerspective(heel_mask,hom,(1280,720))
   mk=(((region>0)&(gray<93))|((heel>0)&(gray<130))).astype('uint8')*255
   mk=cv2.morphologyEx(mk,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
   mk=cv2.dilate(mk,np.ones((9,9),np.uint8))
   clean=cv2.inpaint(fr,mk,5,cv2.INPAINT_NS)
   # Retain fine fabric feel rather than a flat vector-colored patch.
   noise=np.random.default_rng(20261109).normal(0,1.15,clean.shape[:2]);soft=cv2.GaussianBlur(mk.astype('float32')/255,(9,9),2)
   clean=np.clip(clean.astype(float)+(noise*soft)[...,None],0,255).astype('uint8')
   fr=clean;records.append({'frame':idx,'method':'SIFT/RANSAC tracked mask + local inpainting','mask_pixels':int((mk>0).sum())})
   if idx in [3,5,7,9,11,13,15]:Image.fromarray(cv2.cvtColor(fr,cv2.COLOR_BGR2RGB)).save(P/f'sportzz-retouched-shoe-{idx:03}.jpg',quality=95)
  elif idx<5:
   # Heavily motion-blurred initial impact: conservative broad mark-only mask.
   # The transient is too blurred for a defensible object reconstruction. Keep
   # the near-black opening for these two frames, then reveal the clean impact.
   fr=np.zeros_like(fr)+np.array([9,11,8],np.uint8);records.append({'frame':idx,'method':'near-black opening replaces untrackable blurred mark'})
  else:records.append({'frame':idx,'method':'no registration; scene-cut or manual review required'})
 # Start almost black, keeping the first impact readable rather than a branded close-up.
 if idx<3:fr=np.zeros_like(fr)+np.array([9,11,8],np.uint8)
 retouched.append(fr)
p=subprocess.Popen(['/usr/bin/ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','bgr24','-s','1280x720','-r','24','-i','pipe:0','-an','-c:v','libx264','-threads','2','-crf','12','-pix_fmt','yuv420p',str(S/'sportzz-retouched-picture.mp4')],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
for f in retouched:p.stdin.write(f.tobytes())
p.stdin.close();err=p.stderr.read();assert p.wait()==0,err
(S/'sportzz-shoe-retouch-log.json').write_text(json.dumps(records,indent=2))
ims=[P/f'sportzz-retouched-shoe-{idx:03}.jpg' for idx in [3,5,7,9,11,13,15]]
sheet=Image.new('RGB',(1600,2*250),(8,11,9));d=ImageDraw.Draw(sheet)
for i,p in enumerate(ims):
 if p.exists():sheet.paste(Image.open(p).resize((400,225)),(i%4*400,i//4*250));d.text((i%4*400+8,i//4*250+230),p.stem,fill='white')
sheet.save(P/'sportzz-retouched-shoe-review.jpg',quality=95)
print(json.dumps(records,indent=2))
