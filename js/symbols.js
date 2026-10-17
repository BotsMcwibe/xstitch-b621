// Vector chart symbols (symbols/symbols.json, viewBox 100x100) drawn via cached Path2D,
// rasterised per (symbol, pixel size, colour) at devicePixelRatio so they stay sharp at any zoom.
let SYM=null;const P2D={},CACHE=new Map();
export async function loadSymbols(){if(SYM)return SYM;SYM=await (await fetch('symbols/symbols.json')).json();
  for(const [nr,s] of Object.entries(SYM))P2D[nr]=s.els.map(e=>({p:new Path2D(e.d),mode:e.mode,w:e.w}));return SYM;}
export const symUrl=nr=>`symbols/${String(nr).padStart(2,'0')}.svg`;
export function drawSymbolPath(ctx,nr,x,y,size,color='#000'){const els=P2D[nr];if(!els)return;ctx.save();ctx.translate(x,y);ctx.scale(size/100,size/100);
  for(const e of els){if(e.mode==='fill'){ctx.fillStyle=color;ctx.fill(e.p);}else{ctx.strokeStyle=color;ctx.lineWidth=e.w;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke(e.p);}}ctx.restore();}
// cached high-DPI bitmap for one symbol at a CSS pixel size
export function symbolBitmap(nr,size,color='#000'){const dpr=window.devicePixelRatio||1,px=Math.max(1,Math.round(size*dpr)),k=nr+'|'+px+'|'+color;
  let c=CACHE.get(k);if(c)return c;if(CACHE.size>4000)CACHE.clear();
  c=document.createElement('canvas');c.width=c.height=px;drawSymbolPath(c.getContext('2d'),nr,0,0,px,color);CACHE.set(k,c);return c;}
