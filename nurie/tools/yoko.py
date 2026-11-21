# 使い方: python3 nurie/tools/yoko.py  → illustrator/nurie-futsuu-yoko.svg（A4横）を作る
# たて版（nurie-futsuu-nurie.svg）の絵を右に縮めて置き、左に景色を描き足す
import os, math, copy, xml.etree.ElementTree as ET
here = os.path.dirname(os.path.abspath(__file__)); ill = os.path.join(os.path.dirname(here), 'illustrator')
NS = 'http://www.w3.org/2000/svg'; ET.register_namespace('', NS); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
src = ET.parse(os.path.join(ill, 'nurie-futsuu-nurie.svg')).getroot()
parent = {c: p for p in src.iter() for c in p}
W, H = 841.9, 595.3
FX, FY, FW, FH = 25, 22, 792, 483            # 新しい枠
OF = next(e for e in src.iter() if e.get('id') == '_枠')
ox, oy, ow, oh = (float(OF.get(k)) for k in ('x', 'y', 'width', 'height'))
E = 640                                      # 建物を右へ伸ばす先（たて版の座標）
s = FH / oh; tx = 215; ty = FY - oy * s     # tx: たて版の絵を置く位置（左右のバランスで決めた）

root = ET.Element(f'{{{NS}}}svg', {'viewBox': f'0 0 {W} {H}', 'width': '297mm', 'height': '210mm'})
defs = copy.deepcopy(src.find(f'{{{NS}}}defs')); root.append(defs)
cp = ET.SubElement(defs, f'{{{NS}}}clipPath', {'id': 'yoko-frame'})
ET.SubElement(cp, f'{{{NS}}}rect', {'x': str(FX), 'y': str(FY), 'width': str(FW), 'height': str(FH), 'rx': '17'})

L = 'fill:#fff;stroke:#111;stroke-linejoin:round;stroke-linecap:round'
LN = 'fill:none;stroke:#111;stroke-linejoin:round;stroke-linecap:round'
FONT = "font-family:'M PLUS Rounded 1c','Hiragino Maru Gothic ProN',sans-serif;font-weight:800"
def el(parent, tag, style=L, **a):
    a = {k.replace('_', '-'): str(v) for k, v in a.items()}
    if style: a['style'] = style
    return ET.SubElement(parent, f'{{{NS}}}{tag}', a)

frame = el(root, 'g', None, clip_path='url(#yoko-frame)')
el(frame, 'rect', 'fill:#fff;stroke:none', x=FX, y=FY, width=FW, height=FH)
left = el(frame, 'g', None, id='左の景色')
# 太陽
sun = el(left, 'g', None, id='太陽')
el(sun, 'circle', cx=70, cy=74, r=26)
for a in range(0, 360, 45):
    r1, r2 = 35, 46; c, s_ = math.cos(math.radians(a)), math.sin(math.radians(a))
    el(sun, 'line', LN, x1=f'{70+r1*c:.1f}', y1=f'{74+r1*s_:.1f}', x2=f'{70+r2*c:.1f}', y2=f'{74+r2*s_:.1f}')
el(sun, 'circle', 'fill:#111', cx=62, cy=70, r=2.6); el(sun, 'circle', 'fill:#111', cx=78, cy=70, r=2.6)
el(sun, 'path', LN, d='M61,82 Q70,90 79,82')
# 雲と鳥
el(left, 'path', d='M142,118 Q130,94 156,90 Q164,68 192,76 Q214,64 226,86 Q252,86 246,110 Q258,118 242,120 Z', id='雲')
el(left, 'path', LN, d='M262,150 q8,-9 16,0 q8,-9 16,0 M206,182 q6,-7 12,0 q6,-7 12,0', id='鳥')
# 地面
el(left, 'line', LN, x1=FX, y1=455, x2=tx + 30 * s, y2=455, id='地面')
# ドライブスルーの矢印看板と風船
sign = el(left, 'g', None, id='矢印看板')
for (bx, by) in [(92, 208), (152, 194)]:
    el(sign, 'path', LN, d=f'M{bx},{by+35} Q{(bx+126)/2:.0f},{by+55} 126,262')
for (bx, by) in [(92, 208), (152, 194)]:
    el(sign, 'ellipse', cx=bx, cy=by, rx=22, ry=27)
    el(sign, 'path', d=f'M{bx-7},{by+35} L{bx+7},{by+35} L{bx},{by+26} Z')
el(sign, 'rect', x=119, y=310, width=14, height=145)
el(sign, 'path', d='M60,262 L180,262 L208,288 L180,314 L60,314 Q52,314 52,306 L52,270 Q52,262 60,262 Z')
t_ = el(sign, 'text', f'{FONT};font-size:18px;fill:#111;stroke:none', x=124, y=295, text_anchor='middle'); t_.text = 'DRIVE THRU'
# お花
fl = el(left, 'g', None, id='お花')
for fx, fy in [(48, 480), (96, 474), (160, 482), (212, 476)]:
    el(fl, 'line', LN, x1=fx, y1=fy+10, x2=fx, y2=fy+30)
    for a in range(-90, 270, 72):
        el(fl, 'circle', cx=f'{fx+10*math.cos(math.radians(a)):.1f}', cy=f'{fy+10*math.sin(math.radians(a)):.1f}', r=7.5)
    el(fl, 'circle', cx=fx, cy=fy, r=6)

# たて版の絵（枠のクリップと白い背景は外す）
scene_outer = next(e for e in src if e.tag.endswith('}g') and e.get('class'))
scene = copy.deepcopy(list(scene_outer)[0])
for r_ in list(scene):
    if r_.tag.endswith('rect') and r_.get('x') == '17': scene.remove(r_)
wrap = el(frame, 'g', None, id='たて版の絵', transform=f'matrix({s:.4f} 0 0 {s:.4f} {tx:.2f} {ty:.2f})')
wrap.append(scene)
# 建物を右へ伸ばす（たて版では x=569.8 で切れている）
bld = next(e for e in scene.iter() if e.get('id') == '_建物')
for e in list(bld):
    t = e.tag.split('}')[-1]
    if t == 'polygon' and '569.8' in e.get('points', ''):
        e.set('points', e.get('points').replace('569.8', str(E)))
    elif t == 'rect' and e.get('x') == '137.5':
        e.set('width', f'{E - 137.5:.1f}')
    elif t == 'line' and e.get('x2') == '569.8':
        e.set('x2', str(E))
flags = [e for e in bld if e.tag.endswith('path') and e.get('d', '').startswith('M') and 'l-12,22.7' in e.get('d', '')]
last = flags[-1]; fx = 533.9 + 31.9
while fx + 24.1 <= E - 8:
    f = copy.deepcopy(last); f.set('d', f'M{fx:.1f},291h24.1l-12,22.7-12-22.7h0Z'); bld.insert(list(bld).index(last) + 1, f); last = f; fx += 31.9
# 右側: 木・お花・雲・地面
right = el(frame, 'g', None, id='右の景色')
el(right, 'line', LN, x1=tx + E * s, y1=ty + 588.6 * s, x2=FX + FW, y2=ty + 588.6 * s, id='地面')
el(right, 'path', d='M716,96 Q706,76 728,72 Q736,54 760,62 Q780,52 790,72 Q812,72 806,94 Q816,100 802,102 Z', id='雲')
el(right, 'path', LN, d='M680,140 q7,-8 14,0 q7,-8 14,0', id='鳥')
tree = el(right, 'g', None, id='木')
el(tree, 'path', d='M756,470 L760,390 L778,390 L782,470 Z')
el(tree, 'path', d='M728,384 Q712,358 732,342 Q728,312 756,306 Q768,282 794,292 Q820,286 824,316 Q842,330 830,356 Q838,384 812,392 Q796,404 776,396 Q756,406 742,398 Q728,398 728,384 Z')
for cx, cy in [(752, 340), (790, 322), (808, 362), (772, 372)]:
    el(tree, 'circle', cx=cx, cy=cy, r=8)
fl2 = el(right, 'g', None, id='お花2')
for fx_, fy_ in [(738, 482), (800, 478)]:
    el(fl2, 'line', LN, x1=fx_, y1=fy_+10, x2=fx_, y2=fy_+30)
    for a in range(-90, 270, 72):
        el(fl2, 'circle', cx=f'{fx_+10*math.cos(math.radians(a)):.1f}', cy=f'{fy_+10*math.sin(math.radians(a)):.1f}', r=7.5)
    el(fl2, 'circle', cx=fx_, cy=fy_, r=6)
el(root, 'rect', 'fill:none;stroke:#111', id='_枠', x=FX, y=FY, width=FW, height=FH, rx=17)
# なまえ・さい
nb = el(root, 'g', None, id='名前と年齢')
el(nb, 'rect', id='名前欄', x=148, y=518, width=380, height=46, rx=13)
el(nb, 'rect', id='年齢欄', x=543, y=518, width=150, height=46, rx=13)
LB = f'{FONT};font-size:19.8px;fill:#111;stroke:none'
t1 = el(nb, 'text', LB, x=166, y=548); t1.text = 'なまえ'
t2 = el(nb, 'text', LB, x=675, y=548, text_anchor='end'); t2.text = 'さい'
out = os.path.join(ill, 'nurie-futsuu-yoko.svg')
ET.ElementTree(root).write(out, encoding='UTF-8', xml_declaration=True)
print('scale', round(s, 4), 'tx', round(tx, 1), 'ty', round(ty, 1), '->', out)
