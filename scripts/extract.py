import cv2,numpy as np,pickle,sys
from geom import load,peaks
from multiprocessing import Pool
FILE2PAGE={1:10,2:16,3:15,4:14,5:13,6:12,7:11,8:9,9:8,10:7,11:6,12:5,13:4,14:3,15:2,16:1}
COLSTART=[1,113,225,337]; ROWSTART=[1,71,141,211]
def lattice(pos,thk,limit):
  pos=np.array(pos,float); thk=np.array(thk,float)
  d=np.diff(pos); pitch=np.median(d[(d>38)&(d<46)])
  # robust offset: anchor on each pos, count inliers
  best=None
  for a in pos:
    k=np.round((pos-a)/pitch); res=pos-(a+k*pitch); n=(np.abs(res)<5).sum()
    if best is None or n>best[0]: best=(n,a)
  a=best[1]; k=np.round((pos-a)/pitch); inl=np.abs(pos-(a+k*pitch))<5
  A=np.vstack([np.ones(inl.sum()),k[inl]]).T; coef=np.linalg.lstsq(A,pos[inl],rcond=None)[0]
  # refit with tighter tolerance
  for _ in range(2):
    pred=coef[0]+k*coef[1]; inl=np.abs(pos-pred)<4
    A=np.vstack([np.ones(inl.sum()),k[inl]]).T; coef=np.linalg.lstsq(A,pos[inl],rcond=None)[0]
  ks=np.arange(int(k[inl].min()),int(k[inl].max())+1)
  P=[];T=[]
  for kk in ks:
    pr=coef[0]+kk*coef[1]; m=np.where((k==kk)&(np.abs(pos-pr)<4))[0]
    if len(m): j=m[np.argmin(np.abs(pos[m]-pr))]; P.append(pos[j]); T.append(thk[j])
    else: P.append(pr); T.append(0)
  P=np.array(P);T=np.array(T)
  best=max(range(10),key=lambda r: T[np.arange(len(ks))%10==r].mean())
  return P,T,(np.arange(len(ks))%10==best),coef[1]
def npeaks(p,thr):
  idx=np.where(p>thr)[0]; out=[]; s=idx[0]; prev=idx[0]
  for i in list(idx[1:])+[10**9]:
    if i>prev+2:
      if prev-s<=10: out.append((s+prev)/2)
      else:
        # wide run: look for a sharp sub-peak (line) inside using local maxima of profile
        seg=p[s:prev+1]; m=seg.max()
        if m>1.6*np.median(seg): out.append(s+int(np.argmax(seg)))
      s=i
    prev=i
  return np.array(out)
def geom2(name):
  g=load(name); b=(g<120).astype(np.uint8)
  h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(300,1)))
  L=cv2.HoughLinesP(h*255,1,np.pi/3600,400,minLineLength=1200,maxLineGap=30).reshape(-1,4).astype(float)
  ang=np.median(np.degrees(np.arctan2(L[:,3]-L[:,1],L[:,2]-L[:,0])))
  M=cv2.getRotationMatrix2D((g.shape[1]/2,g.shape[0]/2),ang,1)
  g=cv2.warpAffine(g,M,(g.shape[1],g.shape[0]),flags=cv2.INTER_LINEAR,borderValue=255)
  b=(g<120).astype(np.uint8)
  h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(300,1)))
  v=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,300)))
  py=npeaks(h.sum(1),600); px=npeaks(v.sum(0),600)
  def th(img,p,ax):
    s=img[max(0,int(p)-6):int(p)+7,:].sum(1) if ax==0 else img[:,max(0,int(p)-6):int(p)+7].sum(0)
    return int((s>0.15*s.max()).sum()) if s.size and s.max()>0 else 0
  ty=[th(h,p,0) for p in py]; tx=[th(v,p,1) for p in px]
  return g,ang,py,px,ty,tx
def proc(name):
  g,ang,py,px,ty,tx=geom2(name)
  Y,TY,BY,pY=lattice(py,ty,g.shape[0])
  if len(Y)<71:
    Y=np.concatenate([Y,Y[-1]+pY*np.arange(1,72-len(Y))]); BY=np.arange(71)%10==0
  X,TX,BX,pitch=lattice(px,tx,g.shape[1])
  return dict(name=name,g=g,ang=ang,Y=Y,BY=BY,X=X,BX=BX,pitch=pitch,TY=TY,TX=TX)
if __name__=='__main__':
  names=[f'{i}_{s}' for i in range(1,17) for s in (2,1)]
  names=[('16_1_2' if n=='16_1' else n) for n in names]+['16_1']
  with Pool(8) as p: R=p.map(proc,names)
  pickle.dump(R,open('geom.pkl','wb'))
  for r in R:
    print(r['name'],'ang %.2f'%r['ang'],'nY',len(r['Y']),'Y0 %d'%r['Y'][0],'firstboldY',np.argmax(r['BY']),'nX',len(r['X']),'X0 %d Xn %d'%(r['X'][0],r['X'][-1]),'firstboldX',np.argmax(r['BX']),'pitch %.2f'%r['pitch'])
