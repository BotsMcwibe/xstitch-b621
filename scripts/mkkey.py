import numpy as np,csv
from PIL import Image
import os; A=os.environ.get('KEY_PHOTOS_DIR','key_photos/')
B=np.asarray(Image.open(A+'7d97a13bf137a1d9f747c278510bfaaf5de60a8a1ddb8a928c3062fbdcd28526.jpg').convert('RGB')).astype(float)
C=np.asarray(Image.open(A+'bc921040ee9197c0fe69a824c22d708ec2a1f57e92a360f16abc767194d70ef3.jpg').convert('RGB')).astype(float)
runs=[258,321,383,446,510,573,636,700,764,828,892,954,1019,1082,1155,1228,1294,1363,1428,1494,1574,1653,1720,1784,1851,1919,1979,2051,2119,2184,2252,2318,2387,2454,2521,2590,2657,2726,2795,2863,2932,2999,3067,3135,3203,3272,3341,3409,3478,3546,3616,3686,3756]
sym=["three down-triangles (clover)","5","star outline","asterisk cluster (3 small stars)","small open square","half-filled circle (bottom filled)","bold cross / dagger","Roman numeral II (pillar)","outline down-arrow","circle with dot (bullseye)","dollar sign","open circle filled left (crescent)","outline diagonal capsule","spiral / d-curl","small square checker (quartered)","2","flower outline (rosette)","double slash //","diamond with dot","filled heart","percent-like slash with dots","triple-chevron arrow (fletching)","sun outline","equals =","heart outline","sunrise (asterisk over line)","triangle with inner A","script a","bold L","H","four-diamond cluster","infinity loops (oo)","plus +","X with dots (cross of squares)","filled chevron >","script e","hash ### (triple vertical with bars)","filled flower","m","script 8","square filled bottom half","filled A / caret","half-moon (filled left crescent in circle)","italic 6","diamond lattice","outline triangle right","check mark","hatched square","filled right arrow","two filled diamonds","hook-arrow (n with arrow)","arch with centre stem","phi"]
sym+=["double left guillemet «","small filled dot","bold asterisk *","filled diamond","left paren (","anchor","tilde ~","filled diagonal capsule","key / pin (o on stick)","filled circle","filled square"]
cnt=[87,192,247,251,349,358,386,523,598,604,605,631,636,711,751,756,799,806,831,933,963,985,993,1004,1013,1046,1049,1092,1130,1200,1273,1277,1277,1320,1431,1451,1487,1541,1661,1700,1708,1738,1742,1782,1832,2055,2154,2447,2519,2546,2587,2626,3016,3067,3124,3168,3171,3503,5083,5193,5962,6048,6620,7962]
rows=[]
def samp(I,y0,y1,x0,x1,px0,px1):
  s=np.median(I[y0:y1,x0:x1].reshape(-1,3),0); p=np.median(I[y0:y1,px0:px1].reshape(-1,3),0)
  return s, np.clip(s*240/p,0,255)
for i,y in enumerate(runs):
  rows.append(samp(B,y+15,y+45,745,790,900,1000))
for k in range(54,65):
  y=int(1064+(k-54)*100.8)
  rows.append(samp(C,y-12,y+12,460,550,650,750))
with open('key.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['nr','symbol','strands','stitch_count','swatch_rgb_raw_photo','swatch_rgb_whitebalanced','swatch_hex_wb'])
  for i in range(64):
    r,wb=rows[i]; h='#%02x%02x%02x'%tuple(int(v) for v in wb)
    w.writerow([i+1,sym[i],2,cnt[i],' '.join(str(int(v)) for v in r),' '.join(str(int(v)) for v in wb),h])
print(len(sym),sum(cnt),420*280)
