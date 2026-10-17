import numpy as np
S=3; T0,T1=7,35   # template window 28x28
def ink(c): return np.clip((205-np.asarray(c,np.float32))/140,0,1)
def norm(v):
  v=v-v.mean(-1,keepdims=True); return v/(np.linalg.norm(v,axis=-1,keepdims=True)+1e-6)
def build_templates(I,y,w=None,classes=range(1,65)):
  T=[]
  for c in classes:
    s=(y==c) if w is None else ((y==c)&w)
    if s.sum()<3: s=(y==c)
    T.append(np.median(I[s][:,T0:T1,T0:T1],0) if s.sum()<4000 else np.median(I[s][np.random.default_rng(0).choice(np.where(s)[0] if False else np.arange(s.sum()),4000,replace=False)][:,T0:T1,T0:T1],0))
  return np.stack(T)
def score(I,T,chunk=20000):
  Tn=norm(T.reshape(len(T),-1))
  N=len(I); best=np.full((N,len(T)),-1,np.float32)
  for a in range(0,N,chunk):
    B=I[a:a+chunk]
    for dy in range(-S,S+1):
      for dx in range(-S,S+1):
        P=norm(B[:,T0+dy:T1+dy,T0+dx:T1+dx].reshape(len(B),-1))
        best[a:a+chunk]=np.maximum(best[a:a+chunk],P@Tn.T)
  return best
