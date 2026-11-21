# 使い方: python3 nurie/tools/yoko2.py   （一度だけ流す想定）
# 横向き版の車と背景を、参考の絵（丸い車・田の字の窓・ゆるい地面・葉っぱつきのお花）に合わせて作り直す。
# 動物（キリン・ライオン・ゾウ）はそのまま使う。
import os, sys, math, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bbox import bbox, NS
ET.register_namespace('', NS); ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'illustrator', 'nurie-futsuu-yoko.svg')
tree = ET.parse(p); root = tree.getroot()
parent = {c: q for q in root.iter() for c in q}
byid = lambda i: next(e for e in root.iter() if e.get('id') == i)
SH = ('path', 'polygon', 'rect', 'circle', 'ellipse', 'line', 'polyline')
L = 'fill:#fff;stroke:#111;stroke-linejoin:round;stroke-linecap:round'
LN = 'fill:none;stroke:#111;stroke-linejoin:round;stroke-linecap:round'
def el(par, tag, style=L, **a):
    a = {k.replace('_', '-'): str(v) for k, v in a.items()}
    if style: a['style'] = style
    return ET.SubElement(par, f'{{{NS}}}{tag}', a)

# 1) 古い車を消す（「車と動物」の中の 42番以降。1〜20 ゾウ、21〜41 ライオン）
ca = byid('_車と動物'); i = 0
for e in list(ca.iter()):
    if e.tag.split('}')[-1] in SH and bbox(e):
        i += 1
        if i >= 42: parent[e].remove(e)
ca.set('transform', 'translate(0 -22)')          # 動物を少し上へ（車全体を枠に入れるため）

# 2) 新しい車（参考の絵の座標で描いて、0.5倍で置く）
scene = parent[ca]
car = ET.Element(f'{{{NS}}}g', {'id': '車', 'transform': 'matrix(0.5 0 0 0.5 50 23.5)'})
scene.insert(list(scene).index(ca) + 1, car)
el(car, 'ellipse', cx=1240, cy=836, rx=40, ry=64); el(car, 'ellipse', cx=1245, cy=837, rx=16, ry=30)   # うしろのタイヤ
el(car, 'path', d='M1040,762 L1095,737 L1225,697 Q1252,692 1252,722 L1252,808 Q1252,824 1236,830 L1040,880 Z')  # 横
el(car, 'path', d='M1200,736 L1238,723 Q1246,721 1246,729 L1246,733 Q1246,738 1240,740 L1205,751 Q1200,752 1200,747 Z')  # 取っ手
el(car, 'ellipse', cx=1107, cy=872, rx=47, ry=66); el(car, 'ellipse', cx=1110, cy=880, rx=20, ry=34)   # 横の前タイヤ
el(car, 'ellipse', cx=782, cy=900, rx=45, ry=34)                                                   # 前の左タイヤ
el(car, 'path', style=L + ';fill-rule:evenodd',
   d='M822,730 L830,650 Q831,638 845,638 L1112,642 Q1125,643 1125,655 L1125,735 Z '
     'M842,730 L848,662 Q849,655 856,655 L1097,660 Q1104,661 1104,668 L1103,735 Z')                  # フロントガラスの枠
el(car, 'path', d='M705,860 L705,768 Q706,718 762,712 L1095,737 L1040,762 L1040,880 Z')            # 前の面
el(car, 'circle', cx=760, cy=787, r=29); el(car, 'circle', cx=972, cy=797, r=32)                   # ライト
el(car, 'path', d='M822,778 L913,782 Q917,782 917,786 L914,851 Q914,855 910,855 L823,850 Q819,850 819,846 L818,782 Q818,778 822,778 Z')  # ナンバー
el(car, 'path', d='M702,848 L1046,880 Q1062,882 1061,898 L1060,904 Q1058,920 1042,919 L703,896 Q688,894 688,879 L690,861 Q692,847 702,848 Z')  # バンパー

# 3) メニューボード → 田の字の窓
menu = byid('_メニュー'); mp = parent[menu]; idx = list(mp).index(menu); mp.remove(menu)
win = ET.Element(f'{{{NS}}}g', {'id': '窓'}); mp.insert(idx, win)
el(win, 'rect', x=476, y=194, width=122, height=92, rx=4)
el(win, 'rect', x=486, y=204, width=102, height=72)
el(win, 'line', LN, x1=537, y1=204, x2=537, y2=276); el(win, 'line', LN, x1=486, y1=240, x2=588, y2=240)

# 4) 地面の線 → 左右の短い線（植え込み・車・看板のうしろへ続く）
gd = byid('_地面')
for e in list(gd.iter()):
    if e.tag.endswith('line'):
        e.attrib.update({'x1': '25', 'y1': '412', 'x2': '160', 'y2': '398'})
        e2 = ET.Element(e.tag, dict(e.attrib)); e2.attrib.update({'x1': '640', 'y1': '378', 'x2': '817', 'y2': '352'})
        parent[e].append(e2); break

# 5) お花 → 葉っぱつき
fl = byid('_お花2'); fp = parent[fl]; idx = list(fp).index(fl); fp.remove(fl)
fl = ET.Element(f'{{{NS}}}g', {'id': 'お花2'}); fp.insert(idx, fl)
for fx, fy, h in [(742, 408, 30), (792, 430, 28)]:
    el(fl, 'line', LN, x1=fx, y1=fy + 8, x2=fx, y2=fy + 8 + h)
    el(fl, 'path', d=f'M{fx},{fy+8+h*0.7:.1f} Q{fx-16},{fy+8+h*0.35:.1f} {fx-20},{fy+8+h*0.75:.1f} Q{fx-10},{fy+8+h*0.95:.1f} {fx},{fy+8+h*0.7:.1f} Z')
    el(fl, 'path', d=f'M{fx},{fy+8+h*0.55:.1f} Q{fx+16},{fy+8+h*0.2:.1f} {fx+20},{fy+8+h*0.6:.1f} Q{fx+10},{fy+8+h*0.8:.1f} {fx},{fy+8+h*0.55:.1f} Z')
    for a in range(-90, 270, 72):
        el(fl, 'circle', cx=f'{fx+9*math.cos(math.radians(a)):.1f}', cy=f'{fy+9*math.sin(math.radians(a)):.1f}', r=7)
    el(fl, 'circle', cx=fx, cy=fy, r=5.5)
tree.write(p, encoding='UTF-8', xml_declaration=True)
print('ok')
