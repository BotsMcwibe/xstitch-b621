import numpy as np,cv2,pickle,csv
import cells
from extract import COLSTART
R=cells.R; G=pickle.load(open('glyphs.pkl','rb'))
d=np.load('tm.npz'); y=d['y'].reshape(280,420); low=np.load('out_low.npy')
_,info=pickle.load(open('src.pkl','rb'))
ORANGE=(0,159,230)  # BGR of #E69F00
def side(name,page,is_left):
  r=R[name]; g=r['g']; Y=r['Y'][:71]; X=r['X']; i=(page-1)//4; rv0=i*70
  inf=info[page]
  v0=inf['first_left']-1 if is_left else inf['first_right_full']-1
  red=np.full_like(g,255); scan=cv2.cvtColor(g,cv2.COLOR_GRAY2BGR); red=cv2.cvtColor(red,cv2.COLOR_GRAY2BGR)
  for k in range(70):
    for j in range(len(X)-1):
      c=v0+j+1
      if c<1 or c>420: continue
      x0,x1,y0,y1=[int(round(v)) for v in (X[j],X[j+1],Y[k],Y[k+1])]
      gl=cv2.resize(G[int(y[rv0+k,c-1])],(x1-x0-8,y1-y0-8),interpolation=cv2.INTER_AREA)
      red[y0+4:y1-4,x0+4:x1-4]=gl[...,None]
      if low[rv0+k,c-1]:
        for im in (scan,red): cv2.rectangle(im,(x0+1,y0+1),(x1-1,y1-1),ORANGE,4)
  for k,yy in enumerate(Y): cv2.line(red,(int(X[0]),int(yy)),(int(X[-1]),int(yy)),(70,70,70),4 if k%10==0 else 1)
  for j,xx in enumerate(X): cv2.line(red,(int(xx),int(Y[0])),(int(xx),int(Y[70])),(70,70,70),4 if r['BX'][j] else 1)
  out=np.hstack([scan,np.full((g.shape[0],30,3),255,np.uint8),red])
  out=cv2.resize(out,None,fx=0.5,fy=0.5,interpolation=cv2.INTER_AREA)
  cv2.imwrite(f'out/diff_{name}_page{page}.png',out)
  # zoom crop at full res: 15x15 cells region top-left of grid
  ya,yb=int(Y[0]),int(Y[15]); xa,xb=int(X[0]),int(X[min(15,len(X)-1)])
  z=np.hstack([scan[ya:yb,xa:xb],np.full((yb-ya,20,3),255,np.uint8),red[ya:yb,xa:xb]])
  cv2.imwrite(f'out/diff_zoom_{name}_page{page}.png',z)
for nm,p,l in [('16_2',1,True),('1_1',10,False),('13_1',4,False),('10_1',7,False)]: side(nm,p,l)
