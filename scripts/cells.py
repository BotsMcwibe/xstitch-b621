import numpy as np,pickle,cv2,math
from extract import FILE2PAGE,COLSTART,ROWSTART
R={r['name']:r for r in pickle.load(open('geom.pkl','rb'))}
S=42
def page_of(name): return FILE2PAGE[int(name.split('_')[0])]
def bands(p): return (p-1)//4,(p-1)%4
def rowvals(r,p):
  i,_=bands(p); Y=r['Y'][:71]; return Y, ROWSTART[i]-1
def colvals_left(r,p):
  _,j=bands(p); idx=int(np.argmax(r['BX'])); cb=math.ceil((COLSTART[j]-1)/10)*10
  return cb-idx  # boundary value of line 0
def pieces(r,v0,colmin,colmax,Y,rv0):
  """yield (row,col,canvas42,frac,side)"""
  g=r['g'];X=r['X'];W=g.shape[1];out=[]
  for k in range(70):
    y0,y1=int(round(Y[k])),int(round(Y[k+1]))
    for j in range(-1,len(X)):
      c=v0+j+1
      if c<colmin or c>colmax: continue
      if j==-1: xa,xb=0,X[0]; side='L'
      elif j==len(X)-1: xa,xb=X[-1],W; side='R'
      else: xa,xb=X[j],X[j+1]; side='F'
      w=xb-xa
      if side!='F' and w<10: continue
      cell=g[y0:y1,int(round(xa)):int(round(xb))].astype(np.float32)
      cell=cv2.resize(cell,(max(1,int(round(w*S/r['pitch']))),S),interpolation=cv2.INTER_AREA)
      can=np.full((S,S),255,np.float32); frac=1.0
      if side=='F': can=cv2.resize(cell,(S,S),interpolation=cv2.INTER_AREA)
      elif side=='L': ww=min(S,cell.shape[1]); can[:,S-ww:]=cell[:,cell.shape[1]-ww:]; frac=ww/S
      else: ww=min(S,cell.shape[1]); can[:,:ww]=cell[:,:ww]; frac=ww/S
      out.append((rv0+k+1,c,can,frac,side))
  return out
def build(right_name_override=None, use16='16_1_2'):
  grid={}  # (r,c)->list of (canvas,frac,side,name)
  info={}
  for f in range(1,17):
    L=f'{f}_2'; Rn=(use16 if f==16 else f'{f}_1'); p=page_of(L)
    i,j=bands(p); colmin=COLSTART[j]; colmax=(COLSTART[j+1]-1 if j<3 else 420)
    rl=R[L]; Y,rv0=rowvals(rl,p); v0=colvals_left(rl,p)
    lastL=v0+len(rl['X'])-1  # boundary value of last line
    rr=R[Rn]; idx=int(np.argmax(rr['BX']))
    # candidates v0r ≡ (10m-idx); pick nearest to lastL+1
    base=-idx; m=round((lastL+1-base)/10); v0r=base+10*m
    wL=rl['g'].shape[1]-rl['X'][-1]; wR=rr['X'][0]
    lastR=v0r+len(rr['X'])-1
    Yr,_=rowvals(rr,p)
    info[p]=dict(L=L,R=Rn,first_left=v0+1,last_left_full=lastL,first_right_full=v0r+1,last_right=lastR,seam_gap=v0r-lastL,partial_px=(round(float(wL)),round(float(wR))),colmax=colmax,nY=(len(rl['Y']),len(rr['Y'])),boldY_ok=(bool(rl['BY'][0] and rl['BY'][70]) if len(rl['BY'])>70 else False, bool(rr['BY'][0] and rr['BY'][70]) if len(rr['BY'])>70 else False))
    for nm,rec,vv,YY in ((L,rl,v0,Y),(Rn,rr,v0r,Yr)):
      for (rw,c,can,fr,sd) in pieces(rec,vv,colmin,colmax,YY,rv0):
        grid.setdefault((rw,c),[]).append((can,fr,sd,nm))
  return grid,info
def combine(lst):
  full=[x for x in lst if x[2]=='F']
  if full: return full[0][0],1.0,full[0][3]
  can=np.full((S,S),255,np.float32); fr=0
  for c,f,s,n in lst: can=np.minimum(can,c); fr+=f
  return can,min(fr,1.0),'+'.join(x[3] for x in lst)
if __name__=='__main__':
  grid,info=build()
  for p in sorted(info): print(p,info[p])
  missing=[(r,c) for r in range(1,281) for c in range(1,421) if (r,c) not in grid]
  print('cells',len(grid),'missing',len(missing),missing[:20])
  cells=np.zeros((280,420,S,S),np.uint8); frac=np.zeros((280,420)); src=np.empty((280,420),object)
  for (r,c),l in grid.items():
    if 1<=r<=280 and 1<=c<=420:
      can,fr,s=combine(l); cells[r-1,c-1]=can.clip(0,255).astype(np.uint8); frac[r-1,c-1]=fr; src[r-1,c-1]=s
  np.save('cells.npy',cells); np.save('frac.npy',frac); pickle.dump((src,info),open('src.pkl','wb'))
  print('partial cells',(frac<1).sum(), 'frac<0.6',(frac<0.6).sum())
  # 16_1 alt
  g2,_=build(use16='16_1'); alt={k:combine(v) for k,v in g2.items() if any(x[3]=='16_1' for x in v)}
  pickle.dump({k:(v[0].astype(np.uint8),v[1]) for k,v in alt.items()},open('alt16_1.pkl','wb')); print('alt cells',len(alt))
def overlaps():
  grid,_=build(); ov={}
  for k,l in grid.items():
    full=[(x[0].clip(0,255).astype(np.uint8),x[3]) for x in l if x[2]=='F']
    if len(full)>=2: ov[k]=full
    elif len(l)>=2: ov[k]=[(x[0].clip(0,255).astype(np.uint8),x[3]+':'+x[2]) for x in l]
  return ov
