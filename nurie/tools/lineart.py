# 使い方: python3 nurie/tools/lineart.py nurie/illustrator/nurie-futsuu.svg nurie/illustrator/nurie-futsuu-nurie.svg && python3 nurie/tools/embed.py
# イラレで色を塗った絵を、白ぬき＋黒いふち線のぬりえに変換する
import re, sys, xml.etree.ElementTree as ET
src, dst = sys.argv[1], sys.argv[2]
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
tree = ET.parse(src); root = tree.getroot()
style_el = root.find(f'.//{{{NS}}}style')
css = style_el.text
rules = {}
for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', css):
    props = dict((k.strip(), v.strip()) for k, v in (p.split(':', 1) for p in body.split(';') if ':' in p))
    for s in sel.split(','):
        s = s.strip()
        if s.startswith('.'):
            rules.setdefault(s[1:], {}).update(props)
def props_of(el):
    p = {}
    for c in el.get('class', '').split():
        p.update(rules.get(c, {}))
    for k in ('fill', 'stroke', 'stroke-width'):
        if el.get(k): p[k] = el.get(k)
    return p
def lum(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(c*2 for c in h)
    r, g, b = (int(h[i:i+2], 16)/255 for i in range(0, 6, 2))
    return 0.299*r + 0.587*g + 0.114*b
SHAPES = {'path', 'circle', 'rect', 'polygon', 'polyline', 'ellipse', 'line'}
stats = {'outlined': 0, 'kept_dark': 0, 'whitened': 0, 'highlight': 0}
for el in root.iter():
    tag = el.tag.split('}')[-1]
    if tag not in SHAPES: continue
    if any(a.tag.split('}')[-1] == 'clipPath' for a in []): pass
    p = props_of(el)
    fill = p.get('fill', '#000'); stroke = p.get('stroke', 'none')
    if fill == 'none' or tag == 'line' or tag == 'polyline' and fill == 'none':
        continue
    if not fill.startswith('#'): continue
    L = lum(fill)
    if stroke != 'none':
        if L < 0.95:
            el.set('style', 'fill:#fff'); stats['whitened'] += 1
        continue
    OUT = 'fill:#fff;stroke:#111;stroke-width:1.6;stroke-linejoin:round;stroke-linecap:round'
    cls = el.get('class', '')
    thin = (tag == 'polygon' and 'st31' in cls) or ('l1.5,34.1' in el.get('d', ''))
    if thin:
        el.set('style', 'fill:#111'); stats['thin'] = stats.get('thin', 0) + 1
    elif 'st32' in cls:
        el.set('style', OUT); stats['tire'] = stats.get('tire', 0) + 1
    elif L < 0.2:
        el.set('style', 'fill:#111'); stats['kept_dark'] += 1
    elif L > 0.93 and 'st15' in cls:
        el.set('style', 'fill:#fff;stroke:none'); stats['highlight'] += 1
    else:
        el.set('style', 'fill:#fff;stroke:#111;stroke-width:1.6;stroke-linejoin:round;stroke-linecap:round'); stats['outlined'] += 1
# clipPath の中身はスタイル不要
for cp in root.iter(f'{{{NS}}}clipPath'):
    for el in cp.iter():
        if 'style' in el.attrib: del el.attrib['style']
F = "'M PLUS Rounded 1c', 'Hiragino Maru Gothic ProN', sans-serif"
style_el.text = css + f"""
      text {{ font-family: {F} !important; font-weight: 800 !important; }}
      .st14 {{ stroke: #111; stroke-width: 2.4px; stroke-linejoin: round; paint-order: normal; }}
"""
# 丸ゴシックに替えたぶん、文字の位置を中央寄せで合わせる
POS = {'st14': (297.6, 88.6), 'st9': (462, 197.7), 'st6': (462, 197.7), 'st10': (443, 236.7), 'st4': (443, 236.7)}
for t in root.iter(f'{{{NS}}}text'):
    c = t.get('class', '')
    if c in POS:
        x, y = POS[c]; t.set('transform', f'translate({x} {y})'); t.set('text-anchor', 'middle')
tree.write(dst, encoding='UTF-8', xml_declaration=True)
print(stats)
