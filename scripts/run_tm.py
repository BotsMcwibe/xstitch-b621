import numpy as np,csv
from tmatch import *
C=np.load('cells.npy').reshape(-1,42,42); I=ink(C)
y=np.load('pred.npz')['y0']
key={int(r['nr']):int(r['stitch_count']) for r in csv.DictReader(open('key.csv'))}
for it in range(3):
  if it==0: w=None
  else: w=(marg>0.15)
  T=build_templates(I,y,w)
  Sc=score(I,T); o=np.argsort(Sc,1); yp=o[:,-1]+1; srt=np.sort(Sc,1); marg=srt[:,-1]-srt[:,-2]; best=srt[:,-1]
  b=np.bincount(yp,minlength=65)
  print('iter',it,'changed',(yp!=y).sum(),'abs count err',sum(abs(b[n]-key[n]) for n in key),'marg<0.1',(marg<0.1).sum(),'best<0.6',(best<0.6).sum())
  y=yp
np.savez('tm.npz',y=y,score=Sc,marg=marg,best=best,T=T)
