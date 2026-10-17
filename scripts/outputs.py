import numpy as np,csv,cv2,pickle,collections
from tmatch import ink,norm,score,T0,T1
d=np.load('tm.npz'); y=d['y'].reshape(280,420); marg=d['marg'].reshape(280,420); best=d['best'].reshape(280,420); Sc=d['score']
y2=(np.argsort(Sc,1)[:,-2]+1).reshape(280,420); T=d['T']
C=np.load('cells.npy'); frac=np.load('frac.npy'); src,info=pickle.load(open('src.pkl','rb'))
key=list(csv.DictReader(open('key.csv'))); K={int(r['nr']):r for r in key}
conf=np.clip(marg/0.3,0,1)*np.clip((best-0.4)/0.4,0,1)
yy=y.ravel(); mm=np.array([np.median(marg.ravel()[yy==c]) for c in range(1,65)]); mb=np.array([np.median(best.ravel()[yy==c]) for c in range(1,65)])
relm=marg/mm[y-1]; low=(relm<0.6)|(best<mb[y-1]-0.15)|(frac<1)
conf=np.clip(relm,0,1)*np.clip(1-(mb[y-1]-best)/0.3,0,1)*np.where(frac<1,0.5,1)
with open('out/grid.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['row','col','key_nr','symbol','confidence','match_score','margin','second_guess','low_confidence','partial_cell','source_scan'])
  for r in range(280):
    for c in range(420):
      n=int(y[r,c]); w.writerow([r+1,c+1,n,K[n]['symbol'],'%.3f'%conf[r,c],'%.3f'%best[r,c],'%.3f'%marg[r,c],int(y2[r,c]),int(low[r,c]),int(frac[r,c]<1),src[r,c]])
# counts
b=np.bincount(y.ravel(),minlength=65)
with open('out/count_comparison.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['key_nr','symbol','key_count','chart_count','difference','low_conf_cells_of_this_symbol'])
  for n in range(1,65): w.writerow([n,K[n]['symbol'],K[n]['stitch_count'],b[n],b[n]-int(K[n]['stitch_count']),int(low[y==n].sum())])
print('total diff',sum(abs(b[n]-int(K[n]['stitch_count'])) for n in range(1,65)),'low',low.sum(),'partial',(frac<1).sum())
np.save('out_low.npy',low)
# glyph images from templates (28x28 ink) -> 0..255 dark-on-white
G={n:(255-np.clip(T[n-1],0,1)*255).astype(np.uint8) for n in range(1,65)}
pickle.dump(G,open('glyphs.pkl','wb'))
def hexrgb(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def render(color=False,cs=24,margin=60):
  H=280*cs+2*margin; W=420*cs+2*margin
  img=np.full((H,W,3),255,np.uint8)
  for r in range(280):
    for c in range(420):
      n=int(y[r,c]); x0=margin+c*cs; y0=margin+r*cs
      g=cv2.resize(G[n],(cs-4,cs-4),interpolation=cv2.INTER_AREA)
      if color:
        rgb=np.array(hexrgb(K[n]['swatch_hex_wb'])); lum=0.299*rgb[0]+0.587*rgb[1]+0.114*rgb[2]
        cell=np.tile(rgb[::-1],(cs,cs,1)).astype(np.float32)
        a=(255-g.astype(np.float32))/255; inkc=np.array([0,0,0] if lum>110 else [255,255,255],np.float32)
        sub=cell[2:cs-2,2:cs-2]; cell[2:cs-2,2:cs-2]=sub*(1-a[...,None])+inkc*a[...,None]
        img[y0:y0+cs,x0:x0+cs]=cell.astype(np.uint8)
      else:
        img[y0+2:y0+cs-2,x0+2:x0+cs-2]=g[...,None]
  for k in range(421):
    x=margin+k*cs; cv2.line(img,(x,margin),(x,margin+280*cs),(60,60,60),3 if k%10==0 else 1)
    if k%10==0 and k>0: cv2.putText(img,str(k),(x-22,margin-15),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),2); cv2.putText(img,str(k),(x-22,H-margin+35),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),2)
  for k in range(281):
    yy=margin+k*cs; cv2.line(img,(margin,yy),(margin+420*cs,yy),(60,60,60),3 if k%10==0 else 1)
    if k%10==0 and k>0: cv2.putText(img,str(k),(5,yy+8),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),2); cv2.putText(img,str(k),(W-margin+5,yy+8),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,0),2)
  return img
sym=render(False); cv2.imwrite('out/chart_symbols.png',sym)
col=render(True); cv2.imwrite('out/chart_colour_preview.png',col)
# legend image: nr, swatch, glyph, name, counts
L=np.full((64*40+50,1100,3),255,np.uint8)
cv2.putText(L,'nr  swatch glyph  symbol / key count / chart count',(10,30),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
for i in range(64):
  n=i+1; yy=50+i*40; rgb=hexrgb(K[n]['swatch_hex_wb'])
  cv2.putText(L,str(n),(10,yy+27),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,0),2)
  cv2.rectangle(L,(60,yy+5),(130,yy+35),rgb[::-1],-1); cv2.rectangle(L,(60,yy+5),(130,yy+35),(0,0,0),1)
  L[yy+4:yy+36,150:182]=cv2.resize(G[n],(32,32))[...,None]
  cv2.putText(L,f"{K[n]['symbol']}  key {K[n]['stitch_count']}  chart {b[n]}",(200,yy+27),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),1)
cv2.imwrite('out/legend.png',L)
