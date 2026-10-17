#!/usr/bin/env python3
"""Build a chart bundle (single JSON, optionally zipped) for the web viewer.

  Real bundle (run from the private work dir that holds key.csv, tm.npz, cells.npy, ...):
      python scripts/make_bundle.py real --work /path/to/work --out /path/to/work/out/bundle
  Demo bundle (self-made abstract data, safe to publish):
      python scripts/make_bundle.py demo --out demo

Bundle schema (bundle.json):
  {format:"xstitch-bundle", version:1, meta:{title,source,fabric,rows,cols,demo},
   key:[{nr,symbol,count,hex}], glyphs:{nr:"data:image/png;base64,..."},
   grid:{rows,cols,nr:[...row-major...], conf:[0..100 ints], low:[[row,col],...]},
   review:[{row,col,guess,second,conf,crop:"data:image/jpeg;base64,..."}],
   cover:"data:image/jpeg;base64,..." (optional, the pattern's cover picture),
   reference:[{name,page,row0,col0,rows,cols,cell,img:"data:image/jpeg;base64,..."}]}
Rows/cols are 1-based. reference tiles are resampled so each cell is exactly `cell` px.
"""
import argparse,base64,io,json,os,sys,zipfile,csv
import numpy as np
from PIL import Image,ImageDraw

def durl(img,fmt='PNG',q=80):
  b=io.BytesIO(); img.save(b,fmt,**({'quality':q} if fmt=='JPEG' else {}))
  return f"data:image/{fmt.lower()};base64,"+base64.b64encode(b.getvalue()).decode()

def write(bundle,out):
  os.makedirs(out,exist_ok=True)
  js=json.dumps(bundle,separators=(',',':'))
  open(os.path.join(out,'bundle.json'),'w').write(js)
  with zipfile.ZipFile(os.path.join(out,'bundle.zip'),'w',zipfile.ZIP_DEFLATED) as z: z.writestr('bundle.json',js)
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
  bundle={'format':'xstitch-bundle','version':1,
    'meta':{'title':'Luca-S B621','source':'scanned paper chart','fabric':'16 count Aida','rows':280,'cols':420,'demo':False},
    'key':[{'nr':int(k['nr']),'symbol':k['symbol'],'count':int(k['stitch_count']),'hex':k['swatch_hex_wb'],'code':k.get('code','')} for k in key],
    'glyphs':{str(k):v for k,v in glyphs.items()},
    'grid':{'rows':280,'cols':420,'nr':[int(v) for v in y.ravel()],'conf':[int(round(v*100)) for v in conf.ravel()],'low':[[int(r)+1,int(c)+1] for r,c in np.argwhere(low)]},
    'review':review,'reference':ref}
  if cover:
    im=Image.open(cover).convert('RGB'); im.thumbnail((1200,1200)); bundle['cover']=durl(im,'JPEG',82)
  write(bundle,out)

def demo(out,R=40,C=60,cell=16):
  rng=np.random.default_rng(42)
  # viridis-like samples (colorblind safe), made-up names
  hexes=['#440154','#46327e','#365c8d','#277f8e','#1fa187','#4ac16d','#a0da39','#fde725']
  shapes=['circle','square','triangle','diamond','cross','ring','bar','dot']
  names=['Demo Ink','Demo Dusk','Demo Lake','Demo Teal','Demo Sea','Demo Moss','Demo Lime','Demo Sun']
  def glyph(s,sz=28):
    im=Image.new('L',(sz,sz),255); d=ImageDraw.Draw(im); a,b=5,sz-5
    {'circle':lambda:d.ellipse((a,a,b,b),fill=0),'square':lambda:d.rectangle((a,a,b,b),fill=0),
     'triangle':lambda:d.polygon([(sz/2,a),(b,b),(a,b)],fill=0),'diamond':lambda:d.polygon([(sz/2,a),(b,sz/2),(sz/2,b),(a,sz/2)],fill=0),
     'cross':lambda:(d.line((a,a,b,b),fill=0,width=3),d.line((a,b,b,a),fill=0,width=3)),'ring':lambda:d.ellipse((a,a,b,b),outline=0,width=3),
     'bar':lambda:d.rectangle((a,sz/2-3,b,sz/2+3),fill=0),'dot':lambda:d.ellipse((sz/2-3,sz/2-3,sz/2+3,sz/2+3),fill=0)}[s]()
    return im
  G={i+1:glyph(s) for i,s in enumerate(shapes)}
  yy,xx=np.mgrid[0:R,0:C]; field=np.sin(xx/7.0)+np.cos(yy/5.0)+0.6*rng.standard_normal((R,C))
  nr=np.clip(((field-field.min())/(np.ptp(field))*8).astype(int)+1,1,8)
  conf=np.clip(rng.normal(0.9,0.08,(R,C)),0,1); low=np.argwhere(conf<0.72)
  def noisy(g,sz=42):
    can=Image.new('L',(sz,sz),255); can.paste(g,(7,7)); a=np.asarray(can,float)
    a=a*0.85+rng.normal(0,12,a.shape)+20; return Image.fromarray(np.clip(a,0,255).astype(np.uint8))
  review=[]
  for r,c in low:
    n=int(nr[r,c]); s=int(rng.integers(1,9))
    review.append({'row':int(r)+1,'col':int(c)+1,'guess':n,'second':s if s!=n else (n%8)+1,'conf':round(float(conf[r,c]),3),'crop':durl(noisy(G[n]),'JPEG',85)})
  ref=[]
  for half,(c0,c1) in enumerate(((1,30),(31,60))):
    im=Image.new('L',((c1-c0+1)*cell,R*cell),255)
    for r in range(R):
      for c in range(c0,c1+1):
        im.paste(noisy(G[int(nr[r,c-1])]).resize((cell,cell)),((c-c0)*cell,r*cell))
    ref.append({'name':f'demo_half{half+1}','page':1,'row0':1,'col0':c0,'rows':R,'cols':c1-c0+1,'cell':cell,'img':durl(im,'JPEG',75)})
  b=np.bincount(nr.ravel(),minlength=9)
  bundle={'format':'xstitch-bundle','version':1,
    'meta':{'title':'Demo chart (abstract, made-up)','source':'generated by make_bundle.py demo','fabric':'demo','rows':R,'cols':C,'demo':True},
    'key':[{'nr':i+1,'symbol':f'{shapes[i]} ({names[i]})','count':int(b[i+1]) + (1 if i==0 else 0),'hex':hexes[i],'code':f'DEMO-{i+1:02d}'} for i in range(8)],
    'glyphs':{str(k):durl(v) for k,v in G.items()},
    'grid':{'rows':R,'cols':C,'nr':[int(v) for v in nr.ravel()],'conf':[int(round(v*100)) for v in conf.ravel()],'low':[[int(r)+1,int(c)+1] for r,c in low]},
    'review':review,'reference':ref}
  write(bundle,out)

if __name__=='__main__':
  ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['real','demo']); ap.add_argument('--work',default='.'); ap.add_argument('--out',required=True); ap.add_argument('--no-tiles',action='store_true',help='omit scan-derived reference tiles'); ap.add_argument('--cover',help='cover/reference picture to embed')
  a=ap.parse_args(); out=os.path.abspath(a.out)
  real(a.work,out,tiles=not a.no_tiles,cover=a.cover) if a.mode=='real' else demo(out)
