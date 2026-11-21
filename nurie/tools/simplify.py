# 使い方: python3 nurie/tools/simplify.py 元.svg 出力.svg [拡大率] [右へ] [下へ]
# 今回: git show a4eca0f:nurie/illustrator/nurie-futsuu-nurie.svg を元に 1.15 18 22 で実行
# ふつう版を小さい子向けに調整する（一度だけ流す想定）
# - 消す: 車のグリルの縦線・クッキーのつぶ・車の横の細い帯
# - ゾウの鼻のしま: 塗る面 → 短い線に置きかえ
# - 車・ライオン・ゾウ: 枠の右下を基準に拡大
import re, sys, math, os, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbox import bbox, path_pts, NS
ET.register_namespace('', NS); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
src, dst = sys.argv[1], sys.argv[2]; s = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
dx, dy = (float(sys.argv[4]), float(sys.argv[5])) if len(sys.argv) > 5 else (0.0, 0.0)  # 拡大後に右下へずらす量
tree = ET.parse(src); root = tree.getroot()
parent = {c: q for q in root.iter() for c in q}
SH = ('path', 'polygon', 'polyline', 'circle', 'ellipse', 'rect', 'line')
def rb(el):
    b = bbox(el); return [round(v) for v in b] if b else None
REMOVE = [[340,604,344,640],[348,606,352,642],[356,607,360,643],[364,609,368,645],   # グリル
          [455,409,460,414],[467,417,472,422],[457,422,462,427],                      # クッキー
          [543,562,545,563],[543,556,551,562],[535,556,562,572],[500,570,528,586]]    # 車の帯
TRUNK = [[494,480,500,489],[484,488,488,495],[472,492,475,500],[460,492,463,498]]     # ゾウの鼻のしま
for el in list(root.iter()):
    if el.tag.split('}')[-1] not in SH or parent[el].tag.endswith('clipPath'): continue
    b = rb(el)
    if b in REMOVE:
        parent[el].remove(el)
    elif b in TRUNK:
        pts = path_pts(el.get('d')) if el.get('d') else []
        (x1, y1), (x2, y2) = max(((p, q) for p in pts for q in pts), key=lambda pq: math.dist(*pq))
        g = parent[el]; i = list(g).index(el); g.remove(el)
        g.insert(i, ET.Element(f'{{{NS}}}line', {'x1': f'{x1:.1f}', 'y1': f'{y1:.1f}', 'x2': f'{x2:.1f}', 'y2': f'{y2:.1f}',
                 'style': 'fill:none;stroke:#111;stroke-linecap:round'}))
# キリンの斑点を足す（元の素材は斑点が少なく、キリンに見えにくいため）
def blob(cx, cy, w, h):
    rx, ry = w/2, h/2
    return (f'M{cx-rx:.1f},{cy:.1f} C{cx-rx:.1f},{cy-ry*1.1:.1f} {cx+rx*0.2:.1f},{cy-ry*1.2:.1f} {cx+rx:.1f},{cy-ry*0.3:.1f} '
            f'C{cx+rx*1.15:.1f},{cy+ry*0.6:.1f} {cx+rx*0.1:.1f},{cy+ry*1.25:.1f} {cx-rx*0.5:.1f},{cy+ry*0.9:.1f} '
            f'C{cx-rx*0.95:.1f},{cy+ry*0.6:.1f} {cx-rx:.1f},{cy+ry*0.3:.1f} {cx-rx:.1f},{cy:.1f} Z')
win = next(e for e in root.iter() if e.get('id') == '_窓とくま')
target = [e for e in win.iter() if e.tag.endswith('}g')][1]  # 窓の中（クリップされたグループ）
for cx, cy, w, h in [(286, 442, 16, 11), (287, 481, 15, 10)]:
    ET.SubElement(target, f'{{{NS}}}path', {'d': blob(cx, cy, w, h), 'style': 'fill:#fff;stroke:#111;stroke-linejoin:round'})
if s != 1.0:
    frame = next(e for e in root.iter() if e.get('id') == '_枠')
    ax = float(frame.get('x')) + float(frame.get('width')); ay = float(frame.get('y')) + float(frame.get('height'))
    sky = next(e for e in root.iter() if e.get('id') == '_空'); scene = parent[sky]
    kids = list(scene); idx = kids.index(next(e for e in kids if e.get('id') == '_植え込み1'))
    movers = kids[idx + 1:]
    wrap = ET.Element(f'{{{NS}}}g', {'id': '車と動物', 'transform': f'matrix({s} 0 0 {s} {ax*(1-s)+dx:.2f} {ay*(1-s)+dy:.2f})'})
    for m in movers: scene.remove(m); wrap.append(m)
    scene.append(wrap)
tree.write(dst, encoding='UTF-8', xml_declaration=True)
print('ok')
