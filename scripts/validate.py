import numpy as np,csv,cv2,pickle,collections
from tmatch import ink,score
d=np.load('tm.npz'); T=d['T']; y=d['y'].reshape(280,420); Sc=d['score']
y2=(np.argsort(Sc,1)[:,-2]+1).reshape(280,420)
low=np.load('out_low.npy'); C=np.load('cells.npy'); G=pickle.load(open('glyphs.pkl','rb'))
K={int(r['nr']):r for r in csv.DictReader(open('key.csv'))}
src,info=pickle.load(open('src.pkl','rb'))
def classify(cans):
  s=score(ink(np.stack(cans)),T); return s.argmax(1)+1, np.sort(s,1)[:,-1]-np.sort(s,1)[:,-2]
# 1) review sheet
idx=np.argwhere(low); order=np.argsort([d['marg'].reshape(280,420)[r,c] for r,c in idx]); idx=idx[order]
TW=330; per_page=60
for p in range(0,len(idx),per_page):
  chunk=idx[p:p+per_page]; img=np.full((20*60+40,3*TW,3),255,np.uint8)
  cv2.putText(img,'scan crop | best guess glyph (nr) | 2nd guess glyph (nr)',(10,25),cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,0,0),1)
  for t,(r,c) in enumerate(chunk):
    x0=(t//20)*TW; y0=40+(t%20)*60
    img[y0:y0+56,x0+5:x0+61]=cv2.resize(C[r,c],(56,56))[...,None]
    img[y0+4:y0+52,x0+70:x0+118]=cv2.resize(G[int(y[r,c])],(48,48))[...,None]
    img[y0+4:y0+52,x0+180:x0+228]=cv2.resize(G[int(y2[r,c])],(48,48))[...,None]
    cv2.putText(img,f'#{y[r,c]}',(x0+120,y0+25),cv2.FONT_HERSHEY_SIMPLEX,0.55,(0,0,0),1)
    cv2.putText(img,f'#{y2[r,c]}',(x0+230,y0+25),cv2.FONT_HERSHEY_SIMPLEX,0.55,(110,110,110),1)
    cv2.putText(img,f'r{r+1} c{c+1}',(x0+120,y0+48),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,0,0),1)
  cv2.imwrite(f'out/review_low_confidence_{p//per_page+1:02d}.png',img)
print('review pages',(len(idx)+per_page-1)//per_page)
# 2) overlap agreement
ov=pickle.load(open('overlaps.pkl','rb')); rows=[]; agree=0; tot=0
for (r,c),lst in sorted(ov.items()):
  if any(':' in n for _,n in lst): continue
  lab,_=classify([x[0] for x in lst]); tot+=1; ok=len(set(lab))==1; agree+=ok
  rows.append([r,c]+[f'{n}:{l}' for (_,n),l in zip(lst,lab)]+[int(y[r-1,c-1]),int(ok)])
with open('out/seam_overlap_agreement.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['row','col','scanA:nr','scanB:nr','final_nr','agree']); w.writerows(rows)
print('overlap cells',tot,'agree',agree)
# 3) 16_1 vs 16_1_2
alt=pickle.load(open('alt16_1.pkl','rb')); A=[];B=[];keys=[]
for (r,c),(can,fr) in alt.items():
  if fr<1 or src[r-1,c-1]!='16_1_2': continue
  keys.append((r,c)); A.append(can)
la,_=classify(A); lb=np.array([y[r-1,c-1] for r,c in keys])
dis=[(k,a,b) for k,a,b in zip(keys,la,lb) if a!=b]
with open('out/rescan_16_1_vs_16_1_2.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['row','col','nr_from_16_1','nr_from_16_1_2'])
  for (r,c),a,b in dis: w.writerow([r,c,a,b])
print('16_1 vs 16_1_2 cells',len(keys),'disagree',len(dis))
# 4) seam continuity: neighbour agreement across half/page seams vs interior
def same_rate(pairs): return np.mean([y[a]==y[b] for a,b in pairs])
seamcols=set()
for p,i in info.items():
  seamcols.add(i['last_left_full']+ (1 if i['seam_gap']>=1 else 0))
pagecols=[112,224,336]; pagerows=[70,140,210]
interior=same_rate([((r,c),(r,c+1)) for r in range(280) for c in range(0,419,7)])
pc=same_rate([((r,c-1),(r,c)) for r in range(280) for c in pagecols])
pr=same_rate([((r-1,c),(r,c)) for c in range(420) for r in pagerows])
inter_r=same_rate([((r,c),(r+1,c)) for c in range(420) for r in range(5,279,7)])
hs=[]
for p,i in info.items():
  r0=((p-1)//4)*70; c=i['last_left_full']  # boundary between col c and c+1 (1-based) -> idx c-1,c
  hs+= [((r,c-1),(r,c)) for r in range(r0,r0+70)]
hr=same_rate(hs)
with open('out/seam_report.txt','w') as f:
  f.write(f"""Seam / geometry report
Neighbour-agreement rate (fraction of adjacent cell pairs with the same symbol):
  interior horizontal pairs: {interior:.3f}
  interior vertical pairs:   {inter_r:.3f}
  across page column seams (112|113, 224|225, 336|337): {pc:.3f}
  across page row seams (70|71, 140|141, 210|211):      {pr:.3f}
  across scan-half seams inside each A3 page:           {hr:.3f}
A misregistered seam (shifted by a column/row) would drop well below the interior rate.

Overlap cells scanned on both halves: {tot}, agree: {agree}
16_1 vs 16_1_2 rescan of page 1 right half: {len(keys)} cells compared, {len(dis)} disagree

Per-page geometry (first/last columns, seam):
""")
  for p in sorted(info): f.write(f"page {p}: {info[p]}\n")
print(open('out/seam_report.txt').read()[:900])
