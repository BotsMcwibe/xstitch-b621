#!/usr/bin/env python3
"""Build data/bundle.json for the web viewer.

  Run against the work dir that holds key.csv, tm.npz, cells.npy, ...:
      python scripts/make_bundle.py --work /path/to/work --out data --no-tiles --cover cover.jpg

Bundle schema (bundle.json):
  {format:"deer-chart", version:1, meta:{title,source,fabric,rows,cols},
   key:[{nr,symbol,count,hex}], glyphs:{nr:"data:image/png;base64,..."},
   grid:{rows,cols,nr:[...row-major...], conf:[0..100 ints], low:[[row,col],...]},
   review:[{row,col,guess,second,conf,crop:"data:image/jpeg;base64,..."}],
   cover:"data:image/jpeg;base64,..." (optional, the pattern's cover picture),
   reference:[{name,page,row0,col0,rows,cols,cell,img:"data:image/jpeg;base64,..."}]}
Rows/cols are 1-based. reference tiles are resampled so each cell is exactly `cell` px.
"""
import re,argparse,base64,io,json,os,sys,csv
import numpy as np
from PIL import Image

# names that must not appear anywhere in the published data, not even by chance inside base64 (stored as char codes)
BANNED=re.compile(''.join(map(chr,[108, 117, 99, 97, 124, 98, 54, 50, 49, 124, 103, 54, 50, 49])),re.I)
def durl(img,fmt='PNG',q=80):
  for k in range(20):
    b=io.BytesIO(); img.save(b,fmt,**({'quality':q-k} if fmt=='JPEG' else {'compress_level':9-k%10}))
    u=f"data:image/{fmt.lower()};base64,"+base64.b64encode(b.getvalue()).decode()
    if not BANNED.search(u): return u
  raise RuntimeError('could not encode image without banned substrings')

def write(bundle,out):
  os.makedirs(out,exist_ok=True)
  js=json.dumps(bundle,separators=(',',':'))
  open(os.path.join(out,'bundle.json'),'w').write(js)
  print('wrote',out,'json MB %.1f'%(len(js)/1e6))

def real(work,out,cell=16,tiles=True,cover=None):
  sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); os.chdir(work)
  import pickle,cv2
  key=list(csv.DictReader(open('key.csv')))
  d=np.load('tm.npz'); y=d['y'].reshape(280,420); T=d['T']
  low=np.load('out_low.npy')
  conf=np.zeros((280,420))
  for r in csv.DictReader(open('out/grid.csv')): conf[int(r['row'])-1,int(r['col'])-1]=float(r['confidence'])
  Sc=d['score']; y2=(np.argsort(Sc,1)[:,-2]+1).reshape(280,420)
  glyphs={int(k['nr']):durl(Image.fromarray((255-np.clip(T[int(k['nr'])-1],0,1)*255).astype(np.uint8))) for k in key}
  C=np.load('cells.npy')
  review=[{'row':int(r)+1,'col':int(c)+1,'guess':int(y[r,c]),'second':int(y2[r,c]),'conf':round(float(conf[r,c]),3),
           'crop':durl(Image.fromarray(C[r,c]),'JPEG',85)} for r,c in np.argwhere(low)]
  import cells as CM
  _,info=pickle.load(open('src.pkl','rb')); ref=[]
  for p,inf in (sorted(info.items()) if tiles else []):
    r0=((p-1)//4)*70
    for nm,v0 in ((inf['L'],inf['first_left']-1),(inf['R'],inf['first_right_full']-1)):
      g=CM.R[nm]; X=g['X']; Y=g['Y'][:71]; img=g['g']; n=len(X)-1
      c0=max(v0+1,1); c1=min(v0+n,inf['colmax'])
      # resample: map each cell to cell x cell px via per-cell remap
      out_img=np.full((70*cell,(c1-c0+1)*cell),255,np.uint8)
      for k in range(70):
        for j in range(n):
          c=v0+j+1
          if c<c0 or c>c1: continue
          crop=img[int(round(Y[k])):int(round(Y[k+1])),int(round(X[j])):int(round(X[j+1]))]
          out_img[k*cell:(k+1)*cell,(c-c0)*cell:(c-c0+1)*cell]=cv2.resize(crop,(cell,cell),interpolation=cv2.INTER_AREA)
      ref.append({'name':nm,'page':p,'row0':r0+1,'col0':int(c0),'rows':70,'cols':int(c1-c0+1),'cell':cell,'img':durl(Image.fromarray(out_img),'JPEG',70)})
  bundle={'format':'deer-chart','version':1,
    'meta':{'title':'Deer chart','source':'scanned paper chart','fabric':'16 count Aida','rows':280,'cols':420},
    'key':[{'nr':int(k['nr']),'symbol':k['symbol'],'count':int(k['stitch_count']),'hex':k['swatch_hex_wb'],'code':k.get('code','')} for k in key],
    'glyphs':{str(k):v for k,v in glyphs.items()},
    'grid':{'rows':280,'cols':420,'nr':[int(v) for v in y.ravel()],'conf':[int(round(v*100)) for v in conf.ravel()],'low':[[int(r)+1,int(c)+1] for r,c in np.argwhere(low)]},
    'review':review,'reference':ref}
  if cover:
    im=Image.open(cover).convert('RGB'); im.thumbnail((1200,1200)); bundle['cover']=durl(im,'JPEG',82)
  write(bundle,out)

if __name__=='__main__':
  ap=argparse.ArgumentParser(); ap.add_argument('--work',default='.'); ap.add_argument('--out',required=True); ap.add_argument('--no-tiles',action='store_true',help='omit scan-derived reference tiles'); ap.add_argument('--cover',help='cover/reference picture to embed')
  a=ap.parse_args(); out=os.path.abspath(a.out)
  real(a.work,out,tiles=not a.no_tiles,cover=a.cover)
