import numpy as np,pickle,csv
import cells
from tmatch import ink,norm,T0,T1
d=np.load('tm.npz'); T=d['T']  # (64,28,28) ink templates for window [7:35]
grid,_=cells.build(); S=42; TR=4  # trim px at scan edge
res={}
for (r,c),lst in grid.items():
  if any(x[2]=='F' for x in lst): continue
  tot=np.zeros(64); wsum=0; det=[]
  for can,fr,side,nm in lst:
    w=int(round(fr*S))-TR
    if w<6: continue
    I=ink(can)
    # valid canvas columns
    if side=='R': lo,hi=0,w            # piece from left half, occupies left part of cell
    else: lo,hi=S-w,S                  # piece from right half occupies right part
    best=np.full(64,-1.0)
    for dx in range(-7,8):
      for dy in range(-3,4):
        # template placed at canvas cols [T0+dx, T1+dx); compare only overlap with [lo,hi)
        a=max(T0+dx,lo); b=min(T1+dx,hi)
        if b-a<5: continue
        P=I[T0+dy:T1+dy, a:b].ravel()
        Tm=T[:,:,a-(T0+dx):b-(T0+dx)].reshape(64,-1)
        if P.std()<1e-3: s=-(Tm.std(1)>0.05).astype(float)  # blank piece
        else: s=norm(Tm)@norm(P)
        best=np.maximum(best,s)
    tot+=best*(hi-lo); wsum+=hi-lo; det.append((nm,side,w))
  if wsum: res[(r,c)]=(tot/wsum,det)
pickle.dump(res,open('partial_scores.pkl','wb'))
print(len(res))
