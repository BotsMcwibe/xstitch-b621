// Loads the chart data (data/bundle.json) and shared helpers.
export async function loadBundle(){
  const r=await fetch('data/bundle.json',{cache:'no-cache'});
  if(!r.ok)throw new Error('Could not load data/bundle.json ('+r.status+')');
  return r.json();
}
export function keyMap(b){const m={};b.key.forEach(k=>m[k.nr]=k);return m;}
export function loadImages(map){const out={};return Promise.all(Object.entries(map).map(([k,src])=>new Promise(r=>{const i=new Image();i.onload=()=>{out[k]=i;r();};i.onerror=r;i.src=src;}))).then(()=>out);}
// Review corrections are kept in this browser (localStorage) and applied by the viewer and compare pages.
const CK='deerchart:corrections',DK='deerchart:reviewed';
export function getCorr(){try{return JSON.parse(localStorage.getItem(CK))||{};}catch(e){return {};}}
export function getDone(){try{return JSON.parse(localStorage.getItem(DK))||{};}catch(e){return {};}}
export function saveCorr(c,d){try{localStorage.setItem(CK,JSON.stringify(c));localStorage.setItem(DK,JSON.stringify(d));}catch(e){}}
// Starts a page: shows status, loads the data, calls onLoad(bundle).
export function start(onLoad){
  const st=document.getElementById('status');st.textContent='Loading chart…';
  loadBundle().then(b=>{st.textContent=`${b.meta?.title||'Chart'} — ${b.grid.cols}×${b.grid.rows} stitches, ${b.key.length} colours`;onLoad(b);})
    .catch(e=>st.textContent=e.message);
}
