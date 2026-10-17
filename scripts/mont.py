import numpy as np,cv2,sys
C=np.load('cells.npy').reshape(-1,42,42); lab=np.load(sys.argv[1]); K=lab.max()+1
rng=np.random.default_rng(0); per=10; rows_per_img=int(sys.argv[3]) if len(sys.argv)>3 else 30
ids=list(range(K))
for part in range(0,K,rows_per_img):
  img=np.full((rows_per_img*46,70+per*46),255,np.uint8)
  for i,k in enumerate(ids[part:part+rows_per_img]):
    m=np.where(lab==k)[0]
    if len(m)==0: continue
    sel=rng.choice(m,min(per,len(m)),replace=False)
    cv2.putText(img,f'{k}',(2,i*46+28),cv2.FONT_HERSHEY_SIMPLEX,0.6,0,1)
    for t,s in enumerate(sel): img[i*46+2:i*46+44,70+t*46:70+t*46+42]=C[s]
  cv2.imwrite(f'{sys.argv[2]}_{part//rows_per_img}.png',img)
