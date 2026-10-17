#!/usr/bin/env python3
"""Generate the 64 chart symbols as vector SVGs (viewBox 0 0 100 100).

Symbols with a matching Unicode character are converted to outline paths from the
DejaVu fonts at build time, so the site never depends on installed fonts.
The rest are drawn by hand to match the scanned glyphs.
Outputs: symbols/NN.svg, symbols/sprite.svg, symbols/symbols.json
  json: {nr: {"kind":"unicode"|"custom","char","codepoint","font","els":[{"d","mode":"fill"|"stroke","w"}]}}
Usage: python scripts/make_symbols.py [--fonts /usr/share/fonts/truetype/dejavu]
"""
import json,os,sys,argparse
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

U={2:('5','DejaVuSans','h'),3:('☆','DejaVuSans','b'),4:('⁂','DejaVuSans','b'),8:('Ⅱ','DejaVuSerif','b'),9:('⇩','DejaVuSans','b'),
 10:('⊙','DejaVuSans','b'),11:('$','DejaVuSans','h'),16:('2','DejaVuSans','h'),17:('❀','DejaVuSans','b'),20:('♥','DejaVuSans','b'),
 23:('☼','DejaVuSans','b'),24:('=','DejaVuSans','w'),25:('♡','DejaVuSans','b'),28:('ɑ','DejaVuSans','h'),29:('L','DejaVuSans-Bold','h'),
 30:('H','DejaVuSans','h'),31:('❖','DejaVuSans','b'),32:('∞','DejaVuSans','w'),33:('+','DejaVuSans','b'),35:('❯','DejaVuSans','b'),
 36:('e','DejaVuSansMono-Oblique','h'),38:('✿','DejaVuSans','b'),39:('m','DejaVuSans','w'),40:('8','DejaVuSansMono-Oblique','h'),
 42:('Λ','DejaVuSans-Bold','h'),44:('6','DejaVuSansMono-Oblique','h'),46:('▷','DejaVuSans','b'),47:('✓','DejaVuSans','b'),
 49:('➡','DejaVuSans','b'),53:('ϕ','DejaVuSans','h'),54:('«','DejaVuSans','w'),56:('✱','DejaVuSans','b'),57:('◆','DejaVuSans','b'),
 58:('(','DejaVuSans','h'),60:('~','DejaVuSans','w'),63:('●','DejaVuSans','b'),64:('■','DejaVuSans','b')}
# size targets (max extent in viewBox units); small symbols on the chart are drawn smaller
SIZE={11:72,55:20,24:56,60:60,33:60,54:58,58:66,5:40}
def F(d):return {'d':d,'mode':'fill'}
def S(d,w=7):return {'d':d,'mode':'stroke','w':w}
def circ(cx,cy,r):return f'M{cx-r},{cy}a{r},{r} 0 1,0 {2*r},0a{r},{r} 0 1,0 {-2*r},0Z'
def rect(x,y,w,h):return f'M{x},{y}h{w}v{h}h{-w}Z'
C={
 1:[F('M28,14H72L50,46Z'),F('M29,50L48,84H10Z'),F('M71,50L90,84H52Z'),S('M10,47H90',3)],
 5:[S(rect(32,32,36,36),6)],
 6:[S(circ(50,50,30),6),F('M20,50a30,30 0 0,0 60,0Z')],
 7:[F('M43,14h14v20h18v12h-18v40h-14v-40h-18v-12h18Z')],
 12:[S(circ(48,50,27),5),F('M48,23a27,27 0 0,1 0,54a14,27 0 0,0 0,-54Z')],
 13:[S('M22,64L60,26a10,10 0 0,1 14,14L36,78a10,10 0 0,1 -14,-14Z',5)],
 14:[S('M56,14V70a20,20 0 1,1 -20,-20a12,12 0 1,1 10,14a5,5 0 1,1 0,-8',6)],
 15:[S(rect(22,22,56,56),6),F(rect(22,22,28,28)),F(rect(50,50,28,28))],
 18:[S('M22,82L48,18M52,82L78,18',8)],
 19:[S('M50,12L86,50L50,88L14,50Z',6),F('M50,40L60,50L50,60L40,50Z')],
 21:[S('M24,80L76,20',8),F(circ(30,30,8)),F(circ(70,70,8))],
 22:[S('M10,50H90M20,28L36,50L20,72M42,28L58,50L42,72M64,28L80,50L64,72',6)],
 26:[S('M12,82H88M12,70H88M50,62V20M50,62L20,44M50,62L80,44M50,62L32,30M50,62L68,30',6)],
 27:[S('M14,90L50,10L86,90',5),F('M50,50L68,84H32Z')],
 34:[S('M28,28L72,72M72,28L28,72',6),F(rect(14,14,16,16)),F(rect(70,14,16,16)),F(rect(14,70,16,16)),F(rect(70,70,16,16)),F(rect(45,45,10,10))],
 37:[S('M30,14V86M50,14V86M70,14V86M14,50H86',6)],
 41:[S(rect(22,18,56,64),6),F(rect(22,46,56,36))],
 43:[S('M44,20a30,30 0 0,0 0,60',5),F('M52,20a30,30 0 0,1 0,60Z')],
 45:[S('M50,8L92,50L50,92L8,50Z',5),S(circ(50,32,11),5),S(circ(50,68,11),5),S(circ(32,50,11),5),S(circ(68,50,11),5)],
 48:[S(rect(20,20,60,60),6),S('M40,20L80,60M20,20L80,80M20,40L60,80M60,20L80,40M20,60L40,80',5)],
 50:[F('M27,28L49,50L27,72L5,50Z'),F('M73,28L95,50L73,72L51,50Z')],
 51:[S('M30,80V40a20,20 0 0,1 40,0V80',8),F('M14,62H46L30,86Z')],
 52:[S('M22,86V40a28,28 0 0,1 56,0V86M50,12V86',7)],
 55:[F(circ(50,50,9))],
 59:[F('M44,12h12v46h-12Z'),F('M14,50h18a18,18 0 0,0 36,0h18a36,36 0 0,1 -72,0Z')],
 61:[S('M26,74L74,26',24)],
 62:[S('M16,84L58,42',6),S(rect(58,16,24,24),6)],
}
def glyph_path(font,ch,mode,target=74):
  gs=font.getGlyphSet(); name=font.getBestCmap()[ord(ch)]
  bp=BoundsPen(gs); gs[name].draw(bp); x0,y0,x1,y1=bp.bounds
  w,h=x1-x0,y1-y0
  sc=(target/h) if mode=='h' else (target/w) if mode=='w' else target/max(w,h)
  if mode=='h' and w*sc>86: sc=86/w
  if mode=='w' and h*sc>86: sc=86/h
  tx=50-(x0+w/2)*sc; ty=50+(y0+h/2)*sc
  sp=SVGPathPen(gs); gs[name].draw(TransformPen(sp,(sc,0,0,-sc,tx,ty))); return sp.getCommands()
def svg_el(e):
  return f'<path d="{e["d"]}" fill="#000" fill-rule="nonzero"/>' if e['mode']=='fill' else f'<path d="{e["d"]}" fill="none" stroke="#000" stroke-width="{e["w"]}" stroke-linecap="round" stroke-linejoin="round"/>'
if __name__=='__main__':
  ap=argparse.ArgumentParser(); ap.add_argument('--fonts',default='/usr/share/fonts/truetype/dejavu'); ap.add_argument('--out',default='symbols'); a=ap.parse_args()
  fonts={}; out={}
  for nr in range(1,65):
    if nr in U:
      ch,fn,mode=U[nr]; fonts.setdefault(fn,TTFont(os.path.join(a.fonts,fn+'.ttf')))
      out[nr]={'kind':'unicode','char':ch,'codepoint':f'U+{ord(ch):04X}','font':fn,'els':[F(glyph_path(fonts[fn],ch,mode,SIZE.get(nr,74)))]}
    else: out[nr]={'kind':'custom','els':C[nr]}
  os.makedirs(a.out,exist_ok=True); sprite=[]
  for nr,s in out.items():
    body=''.join(svg_el(e) for e in s['els'])
    open(os.path.join(a.out,f'{nr:02d}.svg'),'w').write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">{body}</svg>\n')
    sprite.append(f'<symbol id="s{nr:02d}" viewBox="0 0 100 100">{body}</symbol>')
  open(os.path.join(a.out,'sprite.svg'),'w').write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">'+''.join(sprite)+'</svg>\n')
  json.dump(out,open(os.path.join(a.out,'symbols.json'),'w'),separators=(',',':'))
  print('wrote',len(out),'symbols')
