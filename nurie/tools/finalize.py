# 使い方: python3 nurie/tools/finalize.py  （illustrator/nurie-futsuu-nurie.svg をその場で整える）
# イラレで直したあとに流す。何回流しても同じ結果になる。
# - 線の太さを全部 W にそろえる
# - 見えない白い文字・空の文字を消す
# - 文字をすべて丸ゴシック（M PLUS Rounded 1c 太字）にする
# - 数字だけの文字（看板の「4」など）は白ぬき＋ふち線にして塗れるようにする
import re, os, xml.etree.ElementTree as ET
W = '3.4px'
FONT = "'M PLUS Rounded 1c', 'Hiragino Maru Gothic ProN', sans-serif"
# Helvetica Bold の文字幅（em）。イラレで左寄せ配置された文字の中心を求めるのに使う
HELV = dict(zip('0123456789', [.556]*10)) | {'A': .722, 'B': .722, 'C': .722, 'D': .722, 'E': .667, 'F': .611, 'G': .778,
        'H': .722, 'I': .278, 'J': .556, 'K': .722, 'L': .611, 'M': .833, 'N': .722, 'O': .778, 'P': .667, 'Q': .778,
        'R': .722, 'S': .667, 'T': .611, 'U': .722, 'V': .667, 'W': .944, 'X': .667, 'Y': .667, 'Z': .611, ' ': .278}

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

def set_style(el, **kw):
    cur = [kv for kv in el.get('style', '').split(';') if kv.strip()]
    keys = {k.replace('_', '-') for k in kw}
    cur = [kv for kv in cur if kv.split(':', 1)[0].strip() not in keys]
    cur += [f"{k.replace('_', '-')}:{v}" for k, v in kw.items()]
    el.set('style', ';'.join(cur))

SHAPES = {'path', 'circle', 'rect', 'polygon', 'polyline', 'ellipse', 'line'}
parent = {c: p for p in root.iter() for c in p}
n = 0
for el in list(root.iter()):
    tag = el.tag.split('}')[-1]
    if tag in SHAPES and not parent.get(el, root).tag.endswith('clipPath'):
        if eff(el).get('stroke', 'none') != 'none':
            # 拡大・縮小されたグループの中でも、見た目の線の太さが W になるように割り戻す
            k = 1.0; a = el
            while a in parent:
                a = parent[a]
                m = re.match(r'matrix\(([-\d.]+)', a.get('transform', '')) or re.match(r'scale\(([-\d.]+)', a.get('transform', ''))
                if m: k *= float(m.group(1))
            set_style(el, stroke_width=f'{float(W[:-2])/k:.2f}px'); n += 1
    if tag != 'text':
        continue
    p = eff(el); txt = ''.join(el.itertext()).strip()
    if not txt or (p.get('fill') == '#fff' and p.get('stroke', 'none') == 'none' and not txt.isdigit()):
        parent[el].remove(el); continue
    size = float(p.get('font-size', '20px').rstrip('px'))
    # Helvetica で左寄せされていた英数字は、中心を保ったまま中央寄せにする
    if 'Helvetica' in p.get('font-family', '') and not el.get('text-anchor'):
        m = re.match(r'translate\(([-\d.]+)[ ,]+([-\d.]+)\)', el.get('transform', ''))
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            w = sum(HELV.get(ch, .6) for ch in txt) * size
            el.set('transform', f'translate({x + w/2:.1f} {y})'); el.set('text-anchor', 'middle')
    set_style(el, font_family=FONT, font_weight='800', font_size=f'{size}px')
    if txt.isdigit():
        set_style(el, fill='#fff', stroke='#111', stroke_width=W, stroke_linejoin='round')
tree.write(path, encoding='UTF-8', xml_declaration=True)
print('strokes unified:', n)
