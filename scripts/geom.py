import cv2,numpy as np,json,sys
def load(name):
  g=cv2.imread(f'raw/{name}.bmp',cv2.IMREAD_GRAYSCALE)
  if name.endswith('_1') or name.endswith('_1_2'): g=cv2.rotate(g,cv2.ROTATE_180)
  return g
def peaks(p,thr,gap=3):
  idx=np.where(p>thr)[0]
  if len(idx)==0: return np.array([])
  out=[];s=idx[0];prev=idx[0];
  for i in idx[1:]:
    if i>prev+gap: out.append((s+prev)/2); s=i
    prev=i
  out.append((s+prev)/2); return np.array(out)
def geom(name):
  g=load(name); b=(g<120).astype(np.uint8)
  # deskew using horizontal lines
  h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(300,1)))
  L=cv2.HoughLinesP(h*255,1,np.pi/3600,400,minLineLength=1200,maxLineGap=30)
  L=L.reshape(-1,4).astype(float); ang=np.median(np.degrees(np.arctan2(L[:,3]-L[:,1],L[:,2]-L[:,0])))
  M=cv2.getRotationMatrix2D((g.shape[1]/2,g.shape[0]/2),ang,1)
  g=cv2.warpAffine(g,M,(g.shape[1],g.shape[0]),flags=cv2.INTER_LINEAR,borderValue=255)
  b=(g<120).astype(np.uint8)
  h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(300,1)))
  v=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,300)))
  hp=h.sum(1); vp=v.sum(0)
  py=peaks(hp,600); px=peaks(vp,600)
  # thickness to identify bold
  def thick(prof_img,pos,axis):
    return [int((prof_img[int(p)-6:int(p)+7,:] if axis==0 else prof_img[:,int(p)-6:int(p)+7]).sum(axis=1 if axis==0 else 0).max()>0 and ((prof_img[int(p)-6:int(p)+7,:].sum(1) if axis==0 else prof_img[:,int(p)-6:int(p)+7].sum(0))>0.5*(prof_img.shape[1] if axis==0 else prof_img.shape[0])*0.3).sum()) for p in pos]
  return g,ang,py,px,thick(h,py,0),thick(v,px,1)
if __name__=='__main__':
  for n in sys.argv[1:]:
    g,ang,py,px,ty,tx=geom(n)
    print(n,'ang %.3f'%ang); print(' y',[(int(a),t) for a,t in zip(py,ty)]); print(' x',[(int(a),t) for a,t in zip(px,tx)])
