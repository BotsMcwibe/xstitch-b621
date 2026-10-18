// Minimal zip writer (stored, no compression) and reader (stored + deflate via DecompressionStream). No dependencies.
const CRC=(()=>{const t=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;t[n]=c>>>0;}return t;})();
function crc32(d){let c=0xFFFFFFFF;for(let i=0;i<d.length;i++)c=CRC[(c^d[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;}
const enc=new TextEncoder();
export function makeZip(files){// files: [{name, data: Uint8Array|string}]
  const parts=[],cent=[];let off=0;const now=new Date(),dt=((now.getHours()<<11)|(now.getMinutes()<<5)|(now.getSeconds()>>1)),dd=(((now.getFullYear()-1980)<<9)|((now.getMonth()+1)<<5)|now.getDate());
  for(const f of files){const nm=enc.encode(f.name),d=typeof f.data==='string'?enc.encode(f.data):f.data,c=crc32(d);
    const h=new DataView(new ArrayBuffer(30));h.setUint32(0,0x04034b50,true);h.setUint16(4,20,true);h.setUint16(6,0x0800,true);h.setUint16(8,0,true);h.setUint16(10,dt,true);h.setUint16(12,dd,true);
    h.setUint32(14,c,true);h.setUint32(18,d.length,true);h.setUint32(22,d.length,true);h.setUint16(26,nm.length,true);h.setUint16(28,0,true);parts.push(h,nm,d);
    const ce=new DataView(new ArrayBuffer(46));ce.setUint32(0,0x02014b50,true);ce.setUint16(4,20,true);ce.setUint16(6,20,true);ce.setUint16(8,0x0800,true);ce.setUint16(10,0,true);ce.setUint16(12,dt,true);ce.setUint16(14,dd,true);
    ce.setUint32(16,c,true);ce.setUint32(20,d.length,true);ce.setUint32(24,d.length,true);ce.setUint16(28,nm.length,true);ce.setUint32(42,off,true);cent.push(ce,nm);off+=30+nm.length+d.length;}
  const csz=cent.reduce((a,p)=>a+p.byteLength,0),e=new DataView(new ArrayBuffer(22));e.setUint32(0,0x06054b50,true);e.setUint16(8,files.length,true);e.setUint16(10,files.length,true);e.setUint32(12,csz,true);e.setUint32(16,off,true);
  return new Blob([...parts,...cent,e],{type:'application/zip'});}
export async function readZip(buf){const u=new Uint8Array(buf),v=new DataView(buf);let e=-1;for(let i=u.length-22;i>=Math.max(0,u.length-65558);i--)if(v.getUint32(i,true)===0x06054b50){e=i;break;}
  if(e<0)throw new Error('not a zip file');const n=v.getUint16(e+10,true);let p=v.getUint32(e+16,true);const out=[];const dec=new TextDecoder();
  for(let k=0;k<n;k++){if(v.getUint32(p,true)!==0x02014b50)break;const m=v.getUint16(p+10,true),cs=v.getUint32(p+20,true),nl=v.getUint16(p+28,true),xl=v.getUint16(p+30,true),cl=v.getUint16(p+32,true),lo=v.getUint32(p+42,true);
    const name=dec.decode(u.subarray(p+46,p+46+nl));p+=46+nl+xl+cl;if(name.endsWith('/'))continue;
    const ds=lo+30+v.getUint16(lo+26,true)+v.getUint16(lo+28,true),raw=u.subarray(ds,ds+cs);let data;
    if(m===0)data=raw;else if(m===8){data=new Uint8Array(await new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).arrayBuffer());}else continue;
    out.push({name,data});}return out;}
