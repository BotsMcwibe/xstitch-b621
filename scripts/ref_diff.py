import numpy as np,cv2,csv
import sys; REF=sys.argv[1] if len(sys.argv)>1 else 'reference.png'
ref=cv2.imread(REF)[:,:,::-1].astype(np.float32)/255
R=cv2.resize(ref,(420,280),interpolation=cv2.INTER_AREA)
K=list(csv.DictReader(open('key.csv'))); y=np.load('tm.npz')['y'].reshape(280,420)
pal=np.zeros((65,3),np.float32)
for r in K: h=r['swatch_hex_wb']; pal[int(r['nr'])]=[int(h[1:3],16)/255,int(h[3:5],16)/255,int(h[5:7],16)/255]
def lab(x): return cv2.cvtColor(x.astype(np.float32),cv2.COLOR_RGB2Lab)
Lc=lab(pal[y]).reshape(-1,3); Lr=lab(R).reshape(-1,3)
A=np.hstack([Lc,np.ones((len(Lc),1))]); M=np.linalg.lstsq(A,Lr,rcond=None)[0]
Ln=A@M; dE=np.linalg.norm(Ln-Lr,axis=1).reshape(280,420)
print('median dE %.1f mean %.1f'%(np.median(dE),dE.mean()))
yy=y.ravel(); d=dE.ravel()
# also: which key colour (after normalisation) best fits the ref colour of that key's cells
Pn=np.hstack([lab(pal[1:65][None])[0],np.ones((64,1))])@M
rows=[]
for n in range(1,65):
  s=yy==n; m=d[s].mean(); refmean=Lr[s].mean(0)
  near=np.argsort(np.linalg.norm(Pn-refmean,axis=1))[:3]+1
  rows.append((n,K[n-1]['symbol'],s.sum(),m,np.median(d[s]),list(near)))
mm=np.array([r[3] for r in rows]); med=np.median(mm); mad=np.median(abs(mm-med))
print('per-key mean dE median %.1f MAD %.1f'%(med,mad))
for r in sorted(rows,key=lambda r:-r[3])[:12]:
  print('#%d %-30s n=%d mean %.1f med %.1f z=%.1f  nearest keys to ref colour %s'%(r[0],r[1][:30],r[2],r[3],r[4],(r[3]-med)/(1.4826*mad),r[5]))
