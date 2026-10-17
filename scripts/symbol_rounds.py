# Design rounds for the chart symbols. Each round overrides entries of U / C / SIZE in
# make_symbols.py cumulatively (round N = base + rounds 1..N). PICK selects, per key nr,
# which round's design is the active set in symbols/. Rounds are kept in symbols/rounds/rN.
def F(d):return {'d':d,'mode':'fill'}
def S(d,w=7):return {'d':d,'mode':'stroke','w':w}
def circ(cx,cy,r):return f'M{cx-r},{cy}a{r},{r} 0 1,0 {2*r},0a{r},{r} 0 1,0 {-2*r},0Z'
def rect(x,y,w,h):return f'M{x},{y}h{w}v{h}h{-w}Z'
ROUNDS={}
PICK={n:3 for n in range(1,65)}  # all symbols take their round-3 design (cumulative, so unchanged ones carry over)
import math
def ell(cx,cy,rx,ry,rot=0,n=48):
  c,s=math.cos(math.radians(rot)),math.sin(math.radians(rot));pts=[]
  for i in range(n):
    a=2*math.pi*i/n;x,y=rx*math.cos(a),ry*math.sin(a);pts.append((cx+x*c-y*s,cy+x*s+y*c))
  return 'M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)+'Z'
def spiral(cx,cy,r0,r1,turns,a0=0,n=90):
  pts=[]
  for i in range(n+1):
    t=i/n;a=a0+2*math.pi*turns*t;r=r0+(r1-r0)*t;pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
  return 'M'+'L'.join(f'{x:.1f},{y:.1f}' for x,y in pts)
def rays(cx,cy,r0,r1,half,n,a0=-90):
  d=''
  for i in range(n):
    a=math.radians(a0+360*i/n);ux,uy=math.cos(a),math.sin(a);px,py=-uy,ux
    d+=f'M{cx+ux*r0+px*half:.1f},{cy+uy*r0+py*half:.1f}L{cx+ux*r1:.1f},{cy+uy*r1:.1f}L{cx+ux*r0-px*half:.1f},{cy+uy*r0-py*half:.1f}Z'
  return d
TH=5  # common thin stroke
ROUNDS[1]={'C':{
 1:[F('M32,17H74L53,48Z'),F('M12,50H50L31,79Z'),F('M55,50H94L74,79Z')],
 2:[S('M70,16H35L31,43C42,35 75,36 75,61C75,86 36,90 24,74',TH)],
 8:[S('M12,16Q30,16 30,30V72Q30,78 14,78V86H92V78Q76,78 76,72V30Q76,16 92,16',4),S('M44,22H58V74H44Z',4)],
 9:[S('M38,16H58V54H76L48,82L22,54H38Z',4.5)],
 10:[S(circ(51,48,33),TH),F(circ(51,48,12))],
 13:[S('M58,16H86V38L38,84H24Q14,84 14,74V60Z',4.5)],
 14:[S('M72,16V62'+spiral(48,62,24,3,2.2,0).replace('M','L',1),TH)],
 16:[S('M24,30C30,12 78,10 78,32C78,48 56,58 22,82H82',TH)],
 22:[S('M10,50H92M32,20L12,50L32,78M60,20L40,50L60,78M88,20L68,50L88,78',4.5)],
 23:[S(circ(50,48,28),TH+1),F(rays(50,48,26,40,10,9))],
 25:[S('M50,26C42,12 12,12 12,30C12,50 38,64 50,82C62,64 92,50 92,30C92,12 58,12 50,26Z',4)],
 26:[F(rect(14,55,76,8)),F(rect(14,69,76,8)),S('M50,54V18M50,54L28,32M50,54L72,32M50,54L20,46M50,54L80,46',7)],
 28:[S('M66,32C54,20 24,26 22,56C21,78 46,76 58,58L70,28M70,28C62,50 58,70 70,72C78,73 84,68 88,62',TH)],
 32:[S('M50,50C40,36 32,30 24,32C10,36 10,64 24,68C32,70 40,64 50,50C60,36 68,30 76,32C90,36 90,64 76,68C68,70 60,64 50,50Z',4)],
 36:[S('M30,58C50,58 72,50 72,38C72,26 50,24 38,34C24,46 26,74 44,75C58,76 66,70 74,64',6)],
 40:[S(ell(53,26,11,10,-15),4.5),S(ell(45,60,15,20,20),4.5)],
 42:[F('M50,14C46,14 36,40 34,46H66C64,40 54,14 50,14Z'),S('M38,40L26,86M62,40L76,86',TH)],
 43:[F('M40,16H66Q72,16 72,24V70Q72,78 66,78H40Z'),S('M60,15C36,16 28,34 28,50C28,70 42,86 70,86',4.5)],
 44:[S('M70,16H58C40,18 32,46 34,64C36,84 58,86 66,74C74,62 70,38 54,40C42,42 34,54 34,64',4.5)],
 45:[S('M50,14L87,50L50,87L13,50Z',TH),S('M31,32L69,69M69,32L31,69',TH)],
 48:[S(rect(14,14,76,76),6),S('M14,16L88,90M36,14L90,68M58,14L90,46M14,40L64,90M14,64L40,90',TH)],
 49:[F('M12,36H42V16L90,51L42,86V62H12Z')],
 51:[S('M72,62V24Q72,16 64,16H42Q34,16 34,24V60',7),F('M14,58H52L33,84Z')],
 52:[S('M18,86V40L36,18H66L84,40V86M50,18V86',6)],
 53:[S(ell(51,50,21,25),8),S('M51,14V92',7)],
 54:[S('M48,26L30,48L46,70M71,26L52,48L68,70',4.5)],
 59:[F('M12,48Q22,44 30,52V64Q30,76 46,76Q60,76 60,64V52Q72,42 94,48V66Q94,92 56,94H46Q12,92 12,66Z'),S('M37,14V66M54,14V66',TH)],
 61:[F('M60,14H88Q93,14 93,19V36L44,86H20Q14,86 14,80V58Z')],
 24:[S('M27,36H85M27,62H85',7)],
 18:[S('M18,84L58,16M44,84L88,16',7)],
},'SIZE':{11:84}}
# round 1 also scales/positions every symbol to the averaged scan template (fit by scripts/xf_r1.json)
import json as _j,os as _o
_XF1={int(k):v for k,v in _j.load(open(_o.path.join(_o.path.dirname(_o.path.abspath(__file__)),'xf_r1.json'))).items()}
_XF1[64]=[_XF1[64][0],0,0];_XF1[48]=[_XF1[48][0],0,0]
ROUNDS[1]['XF']=_XF1
# round 2: corrections judged on the real scan crops (the averaged templates are blurred and
# made some symbols too large); better 8 and a square dot as printed.
ROUNDS[2]={'C':{
 40:[S(ell(54,25,10,11,0),4.5),S(ell(48,61,16,22,22),4.5)],
 55:[F(rect(43,42,14,14))],
},'XF':{64:[1,0,0],48:[1,0,0],27:[1.05,0,0],41:[0.95,-2,-3],63:[0.96,-1,-1],23:[0.92,0,2],57:[1,0,0],
 49:[1,0,0],56:[0.88,-2,-2],59:[0.9,0,1],61:[0.92,0,1],6:[1.05,0,0],42:[0.92,0,1],53:[0.95,0,0],45:[0.95,0,0],55:[1,0,0],40:[1,2,0]}}
# round 3: size the solid/filled symbols down to the printed size (they read larger than
# the outline ones), rounded half-disc for 43.
ROUNDS[3]={'C':{
 43:[F('M46,17C66,17 74,32 74,48C74,64 66,79 46,79Z'),S('M58,15C38,16 28,32 28,48C28,66 40,82 62,82',4.5)],
},'XF':{64:[0.82,0,0],63:[0.88,0,0],57:[0.9,0,0],61:[0.88,0,1],41:[0.85,-2,-3],48:[0.9,0,0],6:[0.95,0,0],20:[0.92,0,0],
 49:[0.9,0,0],56:[0.85,-2,-2],59:[0.85,0,1],31:[0.92,0,0],38:[0.92,0,0],15:[0.9,0,0],7:[0.92,0,4],29:[0.9,0,-3],1:[0.92,0,0],43:[1,0,0]}}
