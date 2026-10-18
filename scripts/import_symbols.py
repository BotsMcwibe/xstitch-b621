#!/usr/bin/env python3
"""Import an edited symbol set (zip from symbols.html "Download my set", or a folder of NN.svg files).

  python3 scripts/import_symbols.py my-chart-symbols.zip [--dry-run]

Validates each SVG (number from the file name, parseable, viewBox 0 0 100 100, no scripts/images/text),
flattens shapes and transforms into plain paths, copies changed symbols into symbols/NN.svg, rebuilds
symbols/sprite.svg and symbols/symbols.json, and prints the match score against the scan average
(same metric as symbols.html: 28 px cell, symbol at 86 %, gaussian blur 0.8, NCC).
"""
import argparse, base64, io, json, os, re, sys, tempfile, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
import cairosvg
from svgelements import SVG, Shape, Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMD = os.path.join(ROOT, 'symbols')
BAD = {'script', 'foreignObject', 'image', 'text', 'tspan', 'iframe', 'object', 'embed', 'filter'}
CSS_OK = {'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'stroke-dasharray', 'stroke-opacity',
          'fill-opacity', 'opacity', 'fill-rule', 'clip-rule', 'display', 'visibility'}

def _decls(t):
    out = []
    for d in t.split(';'):
        if ':' not in d: continue
        k, v = d.split(':', 1); k = k.strip().lower(); v = v.replace('!important', '').strip()
        if k in CSS_OK and not re.search(r"url\(\s*['\"]?(?!#)|expression\(|javascript:", v, re.I):
            out.append((k, re.sub(r'px$', '', v) if k in ('stroke-width', 'stroke-miterlimit') else v))
    return out

def inline_styles(root, warns):
    """Inline simple class/tag/id CSS rules from <style> (Illustrator exports) as presentation attributes; drop hidden layers."""
    tag = lambda e: e.tag.split('}')[-1]
    parent = {c: p for p in root.iter() for c in p}
    n = 0; sheets = [e for e in root.iter() if tag(e) == 'style']
    for st in sheets:
        css = re.sub(r'/\*.*?\*/', '', st.text or '', flags=re.S)
        for sels, body in re.findall(r'([^{}]+)\{([^}]*)\}', css):
            ds = _decls(body)
            for sel in (x.strip() for x in sels.split(',')):
                m = re.fullmatch(r'([a-zA-Z]+)?((?:\.[\w-]+)*)|#([\w-]+)', sel)
                if not sel or not m or (not m.group(1) and not m.group(2) and not m.group(3)):
                    if sel: warns.append(f'ignored CSS selector "{sel}"')
                    continue
                cls = [c for c in (m.group(2) or '').split('.') if c]
                for e in root.iter():
                    if m.group(3):
                        ok = e.get('id') == m.group(3)
                    else:
                        ok = (not m.group(1) or tag(e) == m.group(1)) and all(c in (e.get('class') or '').split() for c in cls)
                    if ok:
                        for k, v in ds: e.set(k, v); n += 1
        parent[st].remove(st)
    for e in root.iter():
        if e.get('style'):
            for k, v in _decls(e.get('style')): e.set(k, v)
            del e.attrib['style']
        if e.get('stroke-width'): e.set('stroke-width', re.sub(r'px$', '', e.get('stroke-width')))
        e.attrib.pop('class', None)
    hid = [e for e in root.iter() if e.get('display') == 'none' or e.get('visibility') == 'hidden']
    for e in hid:
        if e in parent: parent[e].remove(e)
    if sheets: warns.append(f'inlined <style> ({n} properties)')
    if hid: warns.append(f'removed {len(hid)} hidden layer(s)/element(s)')
    if any(tag(e) in ('clipPath', 'mask') for e in root.iter()): warns.append('uses clipPath/mask: the flattened paths ignore clipping, check the result')

def nr_from_name(name):
    m = re.match(r'^0*(\d{1,2})(?:[-_ .][^/]*)?\.svg$', os.path.basename(name), re.I)
    n = int(m.group(1)) if m else 0
    return n if 1 <= n <= 64 else None

def templates():
    j = json.load(open(os.path.join(ROOT, 'data', 'sym_templates.json')))
    return {int(k): np.frombuffer(base64.b64decode(v), np.uint8).astype(np.float32).reshape(28, 28) / 255 for k, v in j['t'].items()}

def blur(a, sg=0.8, r=3):
    w = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sg * sg)); w /= w.sum()
    p = np.pad(a, r, mode='reflect')  # reflect == OpenCV BORDER_REFLECT_101
    t = sum(w[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))[r:-r]
    return sum(w[i] * np.pad(t, ((r, r), (0, 0)), mode='reflect')[i:i + a.shape[0]] for i in range(2 * r + 1))

def ink(svg_text, N=28):
    png = cairosvg.svg2png(bytestring=svg_text.encode(), output_width=280, output_height=280, background_color='white')
    a = np.array(Image.open(io.BytesIO(png)).convert('L'), np.float32)
    k = round(0.86 * N); f = 280 / k; o = N // 2 - k // 2; out = np.zeros((N, N), np.float32)
    for y in range(k):
        for x in range(k):
            blk = a[int(y * f):int((y + 1) * f), int(x * f):int((x + 1) * f)]
            out[y + o, x + o] = 1 - blk.mean() / 255
    return blur(out)

def raster_diff(a, b, px=100):
    r = lambda t: np.array(Image.open(io.BytesIO(cairosvg.svg2png(bytestring=t.encode(), output_width=px, output_height=px, background_color='white'))).convert('L'), np.float32) / 255
    return float(np.abs(r(a) - r(b)).mean())

def ncc(a, b):
    a = a - a.mean(); b = b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-9))

def flatten(text):
    """-> (els, warnings). els: [{'d','mode','w'?,'rule'?}] in the 0..100 box."""
    warns = []
    root = ET.fromstring(text)
    for el in list(root.iter()):
        tag = el.tag.split('}')[-1]
        if tag in BAD:
            raise ValueError(f'contains <{tag}> (convert text to paths; no scripts/images)')
        for a in list(el.attrib):
            if a.lower().startswith('on'):
                raise ValueError(f'has an event handler attribute {a}')
    inline_styles(root, warns)
    for k in ('x', 'y'): root.attrib.pop(k, None)
    vb = (root.get('viewBox') or '').replace(',', ' ').split()
    if vb != ['0', '0', '100', '100']:
        warns.append(f'viewBox {" ".join(vb) or "(none)"} rescaled to 0 0 100 100')
        if not vb:
            root.set('viewBox', f"0 0 {root.get('width', '100').rstrip('px')} {root.get('height', '100').rstrip('px')}")
    root.set('width', '100'); root.set('height', '100')
    svg = SVG.parse(io.StringIO(ET.tostring(root, encoding='unicode')), reify=True)
    els = []
    for e in svg.elements():
        if not isinstance(e, Shape):
            continue
        d = Path(e).d()
        if not d.strip():
            continue
        light = lambda c: (0.299 * c.red + 0.587 * c.green + 0.114 * c.blue) > 127
        fill = e.fill is not None and e.fill.value is not None and e.fill.alpha > 0
        stroke = e.stroke is not None and e.stroke.value is not None and e.stroke.alpha > 0 and (e.stroke_width or 0) > 0
        if fill:
            el = {'d': d, 'mode': 'fill'}
            if (e.values.get('fill-rule') or '').strip() == 'evenodd':
                el['rule'] = 'evenodd'
            if light(e.fill): el['knock'] = True  # white fill: erases the ink below (shows the cell background)
            els.append(el)
        if stroke:
            w = getattr(e, 'implicit_stroke_width', None) or e.stroke_width
            el = {'d': d, 'mode': 'stroke', 'w': round(float(w), 2),
                  'cap': (e.values.get('stroke-linecap') or 'butt').strip(), 'join': (e.values.get('stroke-linejoin') or 'miter').strip()}
            if el['join'] == 'miter':
                el['miter'] = float(e.values.get('stroke-miterlimit') or 4)
            if light(e.stroke): el['knock'] = True
            els.append(el)
    if not els:
        raise ValueError('no visible paths')
    return els, warns

def svg_of(els):
    out = []
    for e in els:
        col = '#fff' if e.get('knock') else '#000'
        if e['mode'] == 'fill':
            out.append(f'<path d="{e["d"]}" fill="{col}"' + (' fill-rule="evenodd"' if e.get('rule') else '') + '/>')
        else:
            out.append(f'<path d="{e["d"]}" fill="none" stroke="{col}" stroke-width="{e["w"]}" stroke-linecap="{e.get("cap", "round")}" stroke-linejoin="{e.get("join", "round")}"'
                       + (f' stroke-miterlimit="{e["miter"]}"' if e.get('miter') else '') + '/>')
    return ''.join(out)

def wrap(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">{body}</svg>\n'

def inner(svgtext):
    return re.sub(r'^.*?<svg[^>]*>|</svg>\s*$', '', svgtext, flags=re.S)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args()
    files = {}
    if os.path.isdir(a.src):
        for f in os.listdir(a.src):
            if f.lower().endswith('.svg'): files[f] = open(os.path.join(a.src, f), encoding='utf-8').read()
    else:
        with zipfile.ZipFile(a.src) as z:
            for n in z.namelist():
                if n.lower().endswith('.svg') and '__MACOSX' not in n: files[n] = z.read(n).decode('utf-8')
    SYM = json.load(open(os.path.join(SYMD, 'symbols.json')))
    T = templates(); changed = []; errors = 0; seen = set()
    for name, text in sorted(files.items()):
        nr = nr_from_name(name)
        if not nr:
            print(f'skip  {name}: no symbol number in the name'); continue
        if nr in seen:
            print(f'skip  {name}: #{nr} given twice'); continue
        seen.add(nr)
        try:
            els, warns = flatten(text)
        except Exception as e:
            print(f'ERROR #{nr:2d} {name}: {e}'); errors += 1; continue
        cur = open(os.path.join(SYMD, f'{nr:02d}.svg'), encoding='utf-8').read()
        new = wrap(svg_of(els))
        s0, s1 = ncc(ink(cur), T[nr]), ncc(ink(new), T[nr])
        same = raster_diff(cur, new) < 0.002
        print(f'{"same " if same else "NEW  "} #{nr:2d} score {s0:.3f} -> {s1:.3f} ({s1 - s0:+.3f})' + (f'  [{"; ".join(warns)}]' if warns else ''))
        if not same:
            changed.append(nr)
            SYM[str(nr)] = {'kind': 'custom', 'els': els, 'round': 'import'}
            if not a.dry_run:
                open(os.path.join(SYMD, f'{nr:02d}.svg'), 'w', encoding='utf-8').write(new)
    print(f'{len(changed)} changed: {changed}  errors: {errors}')
    if changed and not a.dry_run:
        json.dump(SYM, open(os.path.join(SYMD, 'symbols.json'), 'w'), ensure_ascii=False)
        sp = ''.join(f'<symbol id="s{n:02d}" viewBox="0 0 100 100">{inner(open(os.path.join(SYMD, f"{n:02d}.svg"), encoding="utf-8").read())}</symbol>' for n in range(1, 65))
        open(os.path.join(SYMD, 'sprite.svg'), 'w', encoding='utf-8').write('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">' + sp + '</svg>\n')
        print('wrote symbols/NN.svg, sprite.svg, symbols.json')
    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
