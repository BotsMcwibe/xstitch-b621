import cv2,numpy as np
im=cv2.imread('raw/16_2.bmp'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
b=(g<110).astype(np.uint8)  # dark ink; watermark is light gray (~180-220)
# deskew via long horizontal lines
h=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(400,1)))
v=cv2.morphologyEx(b,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,120)))
lines=cv2.HoughLinesP(h*255,1,np.pi/1800,500,minLineLength=1500,maxLineGap=20)
L=lines.reshape(-1,4).astype(float); ang=np.degrees(np.arctan2(L[:,3]-L[:,1],L[:,2]-L[:,0]))
print('skew deg median',np.median(ang),'n',len(ang))
def peaks(p,thr):
  idx=np.where(p>thr)[0]; out=[];s=idx[0];prev=idx[0]
  for i in idx[1:]:
    if i>prev+2: out.append((s+prev)/2); s=i
    prev=i
  out.append((s+prev)/2); return np.array(out)
py=peaks(h.sum(1),1000); px=peaks(v.sum(0),1500)
print('rows lines',len(py),'pitch',np.median(np.diff(py)),'std',np.std(np.diff(py)))
print('col lines',len(px),'pitch',np.median(np.diff(px)),'std',np.std(np.diff(px)))
bold=px; pitch=np.median(np.diff(bold))/10; px=np.concatenate([b0+pitch*np.arange(10) for b0 in bold[:-1]]+[bold[-1:]]); print('interp col lines',len(px),'pitch',pitch)
print('x range',px[0],px[-1],'y range',py[0],py[-1])
# line thickness for bold 10-lines
th=[ (h[int(y)-4:int(y)+5,1000]).sum() for y in py]
print('thickness y',th[:25])
np.save('px.npy',px);np.save('py.npy',py)
# sample crop with annotation
x0,y0=int(px[0]),int(py[40]); crop=im[y0:int(py[52]),x0:int(px[12])].copy()
crop=cv2.resize(crop,None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST)
for x in px[:13]: cv2.line(crop,(int((x-x0)*3),0),(int((x-x0)*3),crop.shape[0]),(160,60,0),1) # blue-ish
for y in py[40:53]: cv2.line(crop,(0,int((y-y0)*3)),(crop.shape[1],int((y-y0)*3)),(160,60,0),1)
cv2.imwrite('samples/page1_rows41-52_cols1-12_grid.png',crop)
cells=[]
for r in range(40,46):
  row=[]
  for c in range(0,12):
    cell=g[int(py[r])+3:int(py[r+1])-2,int(px[c])+3:int(px[c+1])-2]
    row.append(cv2.resize(cell,(80,80),interpolation=cv2.INTER_NEAREST))
    row.append(np.full((80,6),255,np.uint8))
  cells.append(np.hstack(row)); cells.append(np.full((6,cells[-1].shape[1]),255,np.uint8))
cv2.imwrite('samples/page1_cells_extracted.png',np.vstack(cells))
