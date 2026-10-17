import numpy as np,pickle,csv,sys
d=dict(np.load('tm_before_fix.npz')); res=pickle.load(open('partial_scores.pkl','rb'))
key={int(r['nr']):int(r['stitch_count']) for r in csv.DictReader(open('key.csv'))}
y=d['y'].copy(); Sc=d['score'].copy(); ch=[]; vis=np.ones(len(y))
for (r,c),v in res.items():
  s=v[0]; i=(r-1)*420+(c-1); vis[i]=v[2]
  if y[i]!=s.argmax()+1: ch.append(((r,c),int(y[i]),int(s.argmax()+1)))
  Sc[i]=s; y[i]=s.argmax()+1
srt=np.sort(Sc,1); d.update(y=y,score=Sc,marg=srt[:,-1]-srt[:,-2],best=srt[:,-1]); np.savez('tm.npz',**d); np.save('visible.npy',vis.reshape(280,420))
b=np.bincount(y,minlength=65); print('changed vs before',len(ch),ch); print('abs err',sum(abs(b[n]-key[n]) for n in key),[(n,int(b[n]-key[n])) for n in key if b[n]!=key[n]])
