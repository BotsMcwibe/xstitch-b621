import numpy as np,cv2
def feat(c):  # c: (...,42,42) uint8
  c=np.asarray(c,np.float32)[...,6:36,6:36]
  ink=np.clip((205-c)/140,0,1)
  sh=ink.shape; f=ink.reshape(-1,30,30)
  out=np.stack([cv2.resize(x,(15,15),interpolation=cv2.INTER_AREA) for x in f])
  out=np.stack([cv2.GaussianBlur(x,(3,3),0.7) for x in out])
  return out.reshape(sh[:-2]+(225,))
