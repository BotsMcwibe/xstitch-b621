import numpy as np,sys
from PIL import Image
import os; A=os.environ.get('KEY_PHOTOS_DIR','key_photos/')
def sw(f,x0,x1,thr):
  a=np.asarray(Image.open(A+f).convert('RGB')).astype(int)
  s=a[:,x0:x1].mean(1); bg=a[:,x1+60:x1+120].mean(1)
  d=np.abs(s-bg).sum(1); mask=d>thr
  runs=[];st=None
  for y,v in enumerate(mask):
    if v and st is None: st=y
    if not v and st is not None:
      if y-st>15: runs.append((st,y))
      st=None
  return [(r,tuple(np.median(a[r[0]+5:r[1]-5,x0+5:x1-5].reshape(-1,3),0).astype(int))) for r in runs]
f=sys.argv[1]; r=sw(f,int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]))
print(len(r))
for i,x in enumerate(r): print(i+1,x)
