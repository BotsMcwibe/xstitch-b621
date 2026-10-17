# Seam/partial cells: rebuild one canvas from both scan pieces (each aligned to its own grid line),
# mask out scanner margin (pure white) and score templates by masked NCC over the visible columns only.
import numpy as np,pickle
import cells
from tmatch import ink,T0,T1
d=np.load('tm.npz'); T=d['T']; S=42
grid,_=cells.build(); res={}
for (r,c),lst in grid.items():
  if any(x[2]=='F' for x in lst): continue
  can=np.zeros((S,S),np.float32); mask=np.zeros(S,bool); det=[]
  for cv,fr,side,nm in lst:
    cm=cv.mean(0); val=np.where(cm<250)[0]
    if len(val)==0: continue
    lo,hi=(0,int(val.max())-1) if side=='R' else (int(val.min())+2,S)
    if hi-lo<3: continue
    can[:,lo:hi]=ink(cv)[:,lo:hi]; mask[lo:hi]=True; det.append((nm,side,hi-lo))
  best=np.full(64,-1.0)
  for dx in range(-4,5):
    for dy in range(-3,4):
      cols=np.arange(T0,T1); src=cols+dx; ok=mask[src]
      if ok.sum()<5: continue
      P=can[T0+dy:T1+dy][:,src[ok]].ravel(); Tm=T[:,:,ok].reshape(64,-1)
      P=P-P.mean(); Tm=Tm-Tm.mean(1,keepdims=True)
      s=(Tm@P)/(np.linalg.norm(Tm,axis=1)*np.linalg.norm(P)+1e-6)
      best=np.maximum(best,s)
  res[(r,c)]=(best,det,mask.sum()/S)
pickle.dump(res,open('partial_scores.pkl','wb')); print(len(res))
