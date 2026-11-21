# 使い方: python3 nurie/tools/finalize.py  （illustrator/nurie-futsuu-nurie.svg をその場で整える）
# - 線の太さを全部 W にそろえる（文字のふち線はそのまま）
# - 見えない白い文字・空の文字を消す
# - 下の欄を「なまえ」「○さい」の2つにする
import re, os, xml.etree.ElementTree as ET
W = '2.2px'
here = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(os.path.dirname(here), 'illustrator', 'nurie-futsuu-nurie.svg')
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
tree = ET.parse(path); root = tree.getroot()
css = root.find(f'.//{{{NS}}}style').text
rules = {}
for sel, body in re.findall(r'([^{}]+)\{([^}]*)\}', css):
    props = dict((k.strip(), v.strip()) for k, v in (p.split(':', 1) for p in body.split(';') if ':' in p))
    for s in sel.split(','):
        s = s.strip()
        if s.startswith('.'): rules.setdefault(s[1:], {}).update(props)
def eff(el):
    p = {}
    for c in el.get('class', '').split(): p.update(rules.get(c, {}))
    for kv in el.get('style', '').split(';'):
        if ':' in kv:
            k, v = kv.split(':', 1); p[k.strip()] = v.strip()
    return p
def set_style(el, k, v):
    items = [kv for kv in el.get('style', '').split(';') if kv.strip() and not kv.strip().startswith(k + ':')]
    items.append(f'{k}:{v}'); el.set('style', ';'.join(items))
SHAPES = {'path', 'circle', 'rect', 'polygon', 'polyline', 'ellipse', 'line'}
parent = {c: p for p in root.iter() for c in p}
n = 0
for el in list(root.iter()):
    tag = el.tag.split('}')[-1]
    if tag in SHAPES and not any(a.tag.endswith('clipPath') for a in [parent.get(el)]):
        if eff(el).get('stroke', 'none') != 'none':
            set_style(el, 'stroke-width', W); n += 1
    if tag == 'text':
        p = eff(el); txt = ''.join(el.itertext()).strip()
        invisible = p.get('fill') == '#fff' and p.get('stroke', 'none') == 'none'
        if not txt or invisible:
            parent[el].remove(el)
# 下の欄
for el in list(root.iter()):
    if el.tag.endswith('rect') and el.get('y') == '758.3' or el.get('id') in ('名前欄', '年齢欄'):
        parent[el].remove(el)
for el in list(root.iter()):
    if el.tag.endswith('text') and ''.join(el.itertext()).strip() in ('なまえ', 'さい'):
        g = parent[el]; g.remove(el)
LBL = "font-family:'M PLUS Rounded 1c','Hiragino Maru Gothic ProN',sans-serif;font-weight:800;font-size:19.8px;fill:#111"
BOX = f'fill:#fff;stroke:#111;stroke-width:{W};stroke-linejoin:round'
g = ET.SubElement(root, f'{{{NS}}}g', {'id': '名前と年齢'})
ET.SubElement(g, f'{{{NS}}}rect', {'id': '名前欄', 'x': '60', 'y': '758.3', 'width': '310', 'height': '51', 'rx': '14.2', 'style': BOX})
ET.SubElement(g, f'{{{NS}}}text', {'x': '78', 'y': '790.9', 'style': LBL}).text = 'なまえ'
ET.SubElement(g, f'{{{NS}}}rect', {'id': '年齢欄', 'x': '386', 'y': '758.3', 'width': '150', 'height': '51', 'rx': '14.2', 'style': BOX})
ET.SubElement(g, f'{{{NS}}}text', {'x': '518', 'y': '790.9', 'text-anchor': 'end', 'style': LBL}).text = 'さい'
# タイトルなしでも上下まん中に来るよう、表示範囲をずらす（枠の上〜名前欄の下）
frame = next(e for e in root.iter() if e.get('id') == '_枠')
top = float(frame.get('y')); bottom = 758.3 + 51
shift = round((top + bottom - 841.9) / 2, 1)
root.set('viewBox', f'0 {shift} 595.3 841.9')
tree.write(path, encoding='UTF-8', xml_declaration=True)
print('strokes unified:', n)
