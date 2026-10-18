// Vector chart symbols (symbols/symbols.json, viewBox 100x100) drawn via cached Path2D,
// rasterised per (symbol, pixel size, colour) at devicePixelRatio so they stay sharp at any zoom.
const RND=new URLSearchParams(location.search).get('round');export const SYMDIR=RND&&/^r\d$/.test(RND)?`symbols/rounds/${RND}/`:'symbols/';
let SYM=null;const P2D={},CACHE=new Map(),OVR={};
// ?localsymbols: use the symbols uploaded on symbols.html (kept in this browser) instead of the published ones. Off by default.
export const LOCALSYM=new URLSearchParams(location.search).has('localsymbols');
async function loadOverrides(){let U={};try{U=JSON.parse(localStorage.getItem('deerchart:symuploads'))||{};}catch(e){}
  await Promise.all(Object.entries(U).map(([nr,u])=>new Promise(r=>{const i=new Image();i.onload=()=>{OVR[nr]=i;r();};i.onerror=r;i.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(u.svg);})));return Object.keys(OVR).length;}
const TINT=new Map();function tinted(nr,px,color){const k=nr+'|'+px+'|'+color;let c=TINT.get(k);if(c)return c;if(TINT.size>3000)TINT.clear();
  c=document.createElement('canvas');c.width=c.height=px;const x=c.getContext('2d');x.drawImage(OVR[nr],0,0,px,px);x.globalCompositeOperation='source-in';x.fillStyle=color;x.fillRect(0,0,px,px);TINT.set(k,c);return c;}
export async function loadSymbols(){if(SYM)return SYM;SYM=await (await fetch(SYMDIR+'symbols.json')).json();
  for(const [nr,s] of Object.entries(SYM)){P2D[nr]=s.els.map(e=>({p:new Path2D(e.d),mode:e.mode,w:e.w,rule:e.rule||'nonzero',knock:!!e.knock,cap:e.cap||'round',join:e.join||'round',miter:e.miter||4}));P2D[nr].t=s.t;}if(LOCALSYM)await loadOverrides();return SYM;}
export const symUrl=nr=>OVR[nr]?OVR[nr].src:`${SYMDIR}${String(nr).padStart(2,'0')}.svg`;
export function drawSymbolPath(ctx,nr,x,y,size,color='#000'){if(OVR[nr]){const px=Math.max(1,Math.ceil(size*Math.abs(ctx.getTransform().a)));ctx.drawImage(tinted(nr,px,color),x,y,size,size);return;}const els=P2D[nr];if(!els)return;ctx.save();ctx.translate(x,y);ctx.scale(size/100,size/100);if(els.t){const [k,tx,ty]=els.t;ctx.translate(50-50*k+tx,50-50*k+ty);ctx.scale(k,k);}
  for(const e of els){ctx.globalCompositeOperation=e.knock?'destination-out':'source-over';if(e.mode==='fill'){ctx.fillStyle=color;ctx.fill(e.p,e.rule);}else{ctx.strokeStyle=color;ctx.lineWidth=e.w;ctx.lineCap=e.cap;ctx.lineJoin=e.join;ctx.miterLimit=e.miter;ctx.stroke(e.p);}}ctx.globalCompositeOperation='source-over';ctx.restore();}
// cached high-DPI bitmap for one symbol at a CSS pixel size
export function symbolBitmap(nr,size,color='#000'){const dpr=window.devicePixelRatio||1,px=Math.max(1,Math.round(size*dpr)),k=nr+'|'+px+'|'+color;
  let c=CACHE.get(k);if(c)return c;if(CACHE.size>4000)CACHE.clear();
  c=document.createElement('canvas');c.width=c.height=px;drawSymbolPath(c.getContext('2d'),nr,0,0,px,color);CACHE.set(k,c);return c;}
