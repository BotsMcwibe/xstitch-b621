import numpy as np,cv2,csv,json
import sys; REF=sys.argv[1] if len(sys.argv)>1 else 'reference.png'
ref=cv2.imread(REF); H,W=ref.shape[:2]
key={int(r['nr']):r['swatch_hex_wb'] for r in csv.DictReader(open('key.csv'))}
y=np.load('tm.npz')['y'].reshape(280,420)
pal=np.zeros((65,3),np.uint8)
for n,h in key.items(): pal[n]=[int(h[5:7],16),int(h[3:5],16),int(h[1:3],16)]
chart=pal[y]  # BGR 280x420
def edges(im):
  g=cv2.GaussianBlur(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32),(0,0),1.0)
  e=np.hypot(cv2.Sobel(g,cv2.CV_32F,1,0),cv2.Sobel(g,cv2.CV_32F,0,1)); e-=e.mean(); return e/(e.std()+1e-6)
ec=edges(chart)
def score(x0,y0,x1,y1):
  r=cv2.resize(ref[y0:y1,x0:x1],(420,280),interpolation=cv2.INTER_AREA); return float((edges(r)*ec).mean())
# border check
g=cv2.cvtColor(ref,cv2.COLOR_BGR2GRAY); print('edge rows/cols mean',g[:3].mean(),g[-3:].mean(),g[:,:3].mean(),g[:,-3:].mean())
best=(-9,None)
for step,rng,c in [(4,24,(0,0,W,H)),(1,5,None)]:
  base=best[1] or c
  for dx0 in range(-rng,rng+1,step):
    for dy0 in range(-rng,rng+1,step):
      x0,y0=base[0]+dx0,base[1]+dy0
      if x0<0 or y0<0: continue
      for dx1 in range(-rng,rng+1,step):
        for dy1 in range(-rng,rng+1,step):
          x1,y1=base[2]+dx1,base[3]+dy1
          if x1>W or y1>H: continue
          if abs((x1-x0)/(y1-y0)-1.5)>0.03: continue
          s=score(x0,y0,x1,y1)
          if s>best[0]: best=(s,(x0,y0,x1,y1))
  print(step,best)
print('full-image score',score(0,0,W,H))
json.dump({'box':best[1],'score':best[0]},open('ref_align.json','w'))
