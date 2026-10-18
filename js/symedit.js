// Symbol editing helpers: editor-friendly SVG export, upload sanitising, match score, upload storage.
export const VB='0 0 100 100';
const NP={M:2,L:2,H:1,V:1,C:6,S:4,Q:4,T:2,A:7,Z:0};
const f2=n=>(Math.round(n*100)/100).toString();
// bake p -> o + k*p into a path (uniform scale), keeping the original commands
export function bakeD(d,k,ox,oy){const tk=d.match(/[MmLlHhVvCcSsQqTtAaZz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?/g)||[];let out=[],i=0,cmd='';
  while(i<tk.length){if(/[a-zA-Z]/.test(tk[i])){cmd=tk[i++];out.push(cmd);if(cmd==='Z'||cmd==='z')continue;}
    const U=cmd.toUpperCase(),abs=cmd===U,n=NP[U];if(!n){i++;continue;}const a=tk.slice(i,i+n).map(Number);i+=n;
    const X=x=>abs?ox+k*x:k*x,Y=y=>abs?oy+k*y:k*y;let r;
    if(U==='H')r=[X(a[0])];else if(U==='V')r=[Y(a[0])];
    else if(U==='A')r=[k*a[0],k*a[1],a[2],a[3],a[4],X(a[5]),Y(a[6])];
    else r=a.map((v,j)=>j%2?Y(v):X(v));
    out.push(r.map(f2).join(' '));if(U==='M')cmd=abs?'L':'l';}
  return out.join(' ').replace(/ ([MmLlHhVvCcSsQqTtAaZz]) /g,'$1').replace(/^([A-Za-z]) /,'$1');}
// editor-friendly SVG from symbols.json: plain paths, transform baked in
export function flatSvg(s){const [k,tx,ty]=s.t||[1,0,0],ox=50-50*k+tx,oy=50-50*k+ty;
  const els=s.els.map(e=>{const d=bakeD(e.d,k,ox,oy);return e.mode==='fill'?`  <path d="${d}" fill="#000"/>`:
    `  <path d="${d}" fill="none" stroke="#000" stroke-width="${f2(e.w*k)}" stroke-linecap="round" stroke-linejoin="round"/>`;});
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VB}" width="100" height="100">\n${els.join('\n')}\n</svg>\n`;}
export const README=`Chart symbols: editing guide
============================
Files: 01.svg ... 64.svg, one per key number (two digits). On upload, 1.svg and 01-anything.svg also work.
Canvas: viewBox "0 0 100 100", 100 x 100 units. Keep this viewBox; anything else is rescaled to fit and flagged.
Safe area: keep ink inside about 8..92 (a 4-8 unit margin). The viewer draws the symbol at 86% of a stitch cell.
Colour: black (#000) only, on a transparent background. Fills and strokes both work.
Strokes: about 5-7 units wide for line symbols (most of the set uses 5-6), round caps and joins.
Keep it plain: paths and basic shapes (rect, circle, ellipse, line, polygon). Avoid transforms, text,
images, filters, masks and external references; text must be converted to outlines/paths.
Similar symbols must stay distinguishable at 12 px (heart vs circle, ( ), arrows, half-moons, 5/6/8/2).
Upload the edited files (or a zip) on symbols.html to see the match score against the scan.
`;
// sanitise an uploaded SVG; returns {svg, warns} or throws
const OK_TAGS=new Set(['svg','g','path','circle','ellipse','rect','line','polyline','polygon','title','desc','defs','clippath','lineargradient','radialgradient','stop','use']);
export function sanitize(text){const warns=[];const doc=new DOMParser().parseFromString(text,'image/svg+xml');
  if(doc.querySelector('parsererror'))throw new Error('not valid SVG/XML');const root=doc.documentElement;if(root.localName!=='svg')throw new Error('root element is not <svg>');
  const walk=el=>{for(const c of [...el.children]){const t=c.localName.toLowerCase();if(!OK_TAGS.has(t)){warns.push(`removed <${c.localName}>`);c.remove();continue;}
      for(const a of [...c.attributes]){const n=a.name.toLowerCase(),v=a.value;
        if(n.startsWith('on')||((n==='href'||n==='xlink:href')&&!v.startsWith('#'))||(/url\(\s*['"]?(?!#)/i.test(v))||/javascript:|expression\(/i.test(v)){c.removeAttribute(a.name);warns.push(`removed attribute ${a.name}`);}}
      if(c.hasAttribute('transform')&&!warns.includes('uses transforms'))warns.push('uses transforms');walk(c);}};
  for(const a of [...root.attributes])if(a.name.toLowerCase().startsWith('on')){root.removeAttribute(a.name);warns.push(`removed attribute ${a.name}`);}walk(root);
  let vb=(root.getAttribute('viewBox')||'').trim().split(/[\s,]+/).map(Number);
  if(vb.length!==4||vb.some(isNaN)){const w=parseFloat(root.getAttribute('width')),h=parseFloat(root.getAttribute('height'));vb=w&&h?[0,0,w,h]:[0,0,100,100];}
  if(vb.join(' ')!==VB){warns.push(`viewBox was "${vb.join(' ')}", rescaled to ${VB}`);const k=100/Math.max(vb[2],vb[3]),tx=(100-vb[2]*k)/2-vb[0]*k,ty=(100-vb[3]*k)/2-vb[1]*k;
    const g=doc.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('transform',`translate(${f2(tx)} ${f2(ty)}) scale(${k})`);while(root.firstChild)g.appendChild(root.firstChild);root.appendChild(g);}
  root.setAttribute('viewBox',VB);root.setAttribute('width','100');root.setAttribute('height','100');root.removeAttribute('style');
  return {svg:new XMLSerializer().serializeToString(root),warns};}
export function nrFromName(name){const b=name.split(/[\\/]/).pop();const m=b.match(/^0*(\d{1,2})(?:[-_ .][^/]*)?\.svg$/i);if(!m)return null;const n=+m[1];return n>=1&&n<=64?n:null;}
// ---- match score: same metric as the design rounds (28 px cell, symbol at 86%, gaussian blur 0.8, NCC vs the scan average)
let TPL=null;export async function templates(){if(TPL)return TPL;const j=await (await fetch('data/sym_templates.json')).json();TPL={};
  for(const [k,b] of Object.entries(j.t)){const s=atob(b),a=new Float32Array(784);for(let i=0;i<784;i++)a[i]=s.charCodeAt(i)/255;TPL[k]=a;}return TPL;}
function loadImg(svg){return new Promise((res,rej)=>{const i=new Image();i.onload=()=>res(i);i.onerror=()=>rej(new Error('SVG failed to render'));i.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);});}
export async function inkOf(svg){const img=await loadImg(svg);const N=28,k=Math.round(0.86*N),o=N/2-k/2;
  const big=document.createElement('canvas');big.width=big.height=280;const bx=big.getContext('2d');bx.fillStyle='#fff';bx.fillRect(0,0,280,280);bx.drawImage(img,0,0,280,280);
  // area-average 280 -> k
  const src=bx.getImageData(0,0,280,280).data,ink=new Float32Array(N*N),f=280/k;
  for(let y=0;y<k;y++)for(let x=0;x<k;x++){let s=0,c=0;for(let yy=Math.floor(y*f);yy<Math.floor((y+1)*f);yy++)for(let xx=Math.floor(x*f);xx<Math.floor((x+1)*f);xx++){s+=src[(yy*280+xx)*4];c++;}ink[(y+o)*N+x+o]=1-s/c/255;}
  return blur(ink,N);}
function blur(a,N){const sg=0.8,r=3,w=[];let t=0;for(let i=-r;i<=r;i++){const v=Math.exp(-i*i/(2*sg*sg));w.push(v);t+=v;}for(let i=0;i<w.length;i++)w[i]/=t;
  const R=i=>{if(i<0)return -i;if(i>=N)return 2*N-2-i;return i;},tmp=new Float32Array(N*N),out=new Float32Array(N*N);
  for(let y=0;y<N;y++)for(let x=0;x<N;x++){let s=0;for(let j=-r;j<=r;j++)s+=w[j+r]*a[y*N+R(x+j)];tmp[y*N+x]=s;}
  for(let y=0;y<N;y++)for(let x=0;x<N;x++){let s=0;for(let j=-r;j<=r;j++)s+=w[j+r]*tmp[R(y+j)*N+x];out[y*N+x]=s;}return out;}
export function ncc(a,b){let ma=0,mb=0;for(let i=0;i<a.length;i++){ma+=a[i];mb+=b[i];}ma/=a.length;mb/=b.length;let s=0,sa=0,sb=0;
  for(let i=0;i<a.length;i++){const x=a[i]-ma,y=b[i]-mb;s+=x*y;sa+=x*x;sb+=y*y;}return s/Math.sqrt(sa*sb+1e-9);}
export async function score(svg,nr){const T=await templates();return ncc(await inkOf(svg),T[nr]);}
export async function sameInk(a,b){const x=await inkOf(a),y=await inkOf(b);let d=0;for(let i=0;i<x.length;i++)d+=Math.abs(x[i]-y[i]);return d/x.length<0.003;}
// ---- uploads kept in this browser
const UK='deerchart:symuploads';
export function getUploads(){try{return JSON.parse(localStorage.getItem(UK))||{};}catch(e){return {};}}
export function setUploads(u){localStorage.setItem(UK,JSON.stringify(u));}
