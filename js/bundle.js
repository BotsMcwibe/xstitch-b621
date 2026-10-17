// Shared chart-bundle loader: file picker / drag-drop (zip or json), IndexedDB memory, optional ./data-private/bundle.json
const DB='xstitch',STORE='kv';
function idb(){return Promise.race([idbOpen(),new Promise((_,rej)=>setTimeout(()=>rej(new Error('IndexedDB unavailable')),2000))]);}
function idbOpen(){return new Promise((res,rej)=>{const r=indexedDB.open(DB,1);r.onupgradeneeded=()=>r.result.createObjectStore(STORE);r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});}
export async function kvGet(k){let db;try{db=await idb();}catch(e){return undefined;}return new Promise(r=>{const q=db.transaction(STORE).objectStore(STORE).get(k);q.onsuccess=()=>r(q.result);q.onerror=()=>r(undefined);});}
export async function kvSet(k,v){let db;try{db=await idb();}catch(e){return;}return new Promise(r=>{const t=db.transaction(STORE,'readwrite');t.objectStore(STORE).put(v,k);t.oncomplete=()=>r();});}
// minimal zip reader (stored + deflate) using DecompressionStream
async function unzipFirstJson(buf){
  const dv=new DataView(buf);let e=buf.byteLength-22;
  while(e>=0&&dv.getUint32(e,true)!==0x06054b50)e--; if(e<0)throw new Error('Not a zip file');
  const n=dv.getUint16(e+10,true);let p=dv.getUint32(e+16,true);
  for(let i=0;i<n;i++){
    const method=dv.getUint16(p+10,true),csize=dv.getUint32(p+20,true),fnl=dv.getUint16(p+28,true),xl=dv.getUint16(p+30,true),cl=dv.getUint16(p+32,true),off=dv.getUint32(p+42,true);
    const name=new TextDecoder().decode(new Uint8Array(buf,p+46,fnl));p+=46+fnl+xl+cl;
    if(!name.endsWith('.json'))continue;
    const lo=off+30+dv.getUint16(off+26,true)+dv.getUint16(off+28,true);const data=new Uint8Array(buf,lo,csize);
    if(method===0)return new TextDecoder().decode(data);
    if(method===8){const s=new Blob([data]).stream().pipeThrough(new DecompressionStream('deflate-raw'));return await new Response(s).text();}
    throw new Error('Unsupported zip compression '+method);
  }
  throw new Error('No .json inside zip');
}
export async function parseFile(file){
  const buf=await file.arrayBuffer();const u=new Uint8Array(buf,0,2);
  const text=(u[0]===0x50&&u[1]===0x4b)?await unzipFirstJson(buf):new TextDecoder().decode(buf);
  return validate(JSON.parse(text));
}
function validate(b){if(!b||b.format!=='xstitch-bundle'||!b.grid||!b.key)throw new Error('This file is not a chart bundle');return b;}
// Load order: remembered bundle (IndexedDB) -> ./data-private/bundle.json -> ./data/bundle.json (published default)
export async function loadInitial(){
  const saved=await kvGet('bundle'); if(saved) return {bundle:saved,from:'remembered'};
  for(const u of ['data-private/bundle.json','data/bundle.json']){
    try{const r=await fetch(u,{cache:'no-store'});if(r.ok)return {bundle:validate(await r.json()),from:u};}catch(e){}
  }
  return {bundle:null,from:null};
}
export async function loadDemo(){const r=await fetch('demo/bundle.json');return validate(await r.json());}
// Wires the picker bar shared by all pages. onLoad(bundle, sourceLabel)
export function setupPicker(onLoad){
  const bar=document.getElementById('bundlebar');
  bar.innerHTML=`<label class="btn">Open chart bundle…<input type="file" accept=".zip,.json,application/json,application/zip" hidden></label>
   <button class="btn" id="demoBtn">Load demo</button><button class="btn" id="forgetBtn">Back to default chart</button>
   <span id="bundleStatus">Drop a bundle (.zip or .json) anywhere on the page.</span>`;
  const status=bar.querySelector('#bundleStatus');
  const use=async(b,label,remember)=>{if(remember){try{await kvSet('bundle',b);}catch(e){label+=' (could not remember it: '+e.message+')';}}
    status.textContent=`Loaded: ${b.meta?.title||'bundle'} — ${b.grid.cols}×${b.grid.rows} stitches, ${b.key.length} colours (${label})`;onLoad(b);};
  const fromFile=async f=>{try{status.textContent='Reading '+f.name+'…';await use(await parseFile(f),f.name,true);}catch(e){status.textContent='Could not open: '+e.message;}};
  bar.querySelector('input').onchange=e=>e.target.files[0]&&fromFile(e.target.files[0]);
  bar.querySelector('#demoBtn').onclick=async()=>use(await loadDemo(),'demo',false);
  bar.querySelector('#forgetBtn').onclick=async()=>{await kvSet('bundle',undefined);location.reload();};
  addEventListener('dragover',e=>{e.preventDefault();document.body.classList.add('drag');});
  addEventListener('dragleave',()=>document.body.classList.remove('drag'));
  addEventListener('drop',e=>{e.preventDefault();document.body.classList.remove('drag');const f=e.dataTransfer.files[0];if(f)fromFile(f);});
  loadInitial().then(({bundle,from})=>{if(bundle)use(bundle,from,false);else status.textContent='No bundle loaded. Open one, drop one here, or load the demo.';});
}
export function keyMap(b){const m={};b.key.forEach(k=>m[k.nr]=k);return m;}
export function loadImages(map){const out={};return Promise.all(Object.entries(map).map(([k,src])=>new Promise(r=>{const i=new Image();i.onload=()=>{out[k]=i;r();};i.onerror=r;i.src=src;}))).then(()=>out);}
// Corrections made in review.html are kept per bundle title
export const corrKey=b=>'corr:'+(b.meta?.title||'bundle')+':'+b.grid.cols+'x'+b.grid.rows;
