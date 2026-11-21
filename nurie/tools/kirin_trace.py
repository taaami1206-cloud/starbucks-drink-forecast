# 使い方（一度きり）: <potracer入りのpython> nurie/tools/kirin_trace.py <参考画像.png>
# 参考画像（1536x1024）の「きりんの窓」部分をなぞってベクターにし、
# 横版 illustrator/nurie-futsuu-yoko.svg の <g id="_窓とくま">…</g> と入れ替える。
# 参考画像の窓の外枠（x427〜786, 上334.5〜窓台下677）を、今の窓（x266.7〜432.3, y210.5〜371.4）に合わせる。
import os, re, sys
import numpy as np, potrace
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); svgp = os.path.join(os.path.dirname(here), 'illustrator', 'nurie-futsuu-yoko.svg')
X0, Y0, X1, Y1 = 412, 312, 802, 690   # 切り出し範囲（参考画像の座標）
UP = 3
im = Image.open(sys.argv[1]).convert('L').crop((X0, Y0, X1, Y1))
im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS)
plist = potrace.Bitmap(np.array(im) >= 128).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.2)
def dpath(c):
    s = f'M{c.start_point.x:.1f},{c.start_point.y:.1f}'
    for seg in c.segments:
        if seg.is_corner: s += f'L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}'
        else: s += f'C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}'
    return s + 'Z'
kx = (432.3 - 266.7) / (786 - 427); ky = (371.4 - 210.5) / (677 - 334.5)
tx = 266.7 + (X0 - 427) * kx; ty = 210.5 + (Y0 - 334.5) * ky
d = ''.join(dpath(c) for c in plist)
grp = (f'<g id="_窓ときりん">\n'
       f'              <rect x="266.7" y="210.5" width="165.6" height="149" style="fill:#fff" /><rect x="260.1" y="359.4" width="178.8" height="12" style="fill:#fff" />\n'
       f'              <path transform="matrix({kx/UP:.6f} 0 0 {ky/UP:.6f} {tx:.2f} {ty:.2f})" style="fill:#111;fill-rule:evenodd;stroke:none" d="{d}" />\n'
       f'            </g>')
s = open(svgp, encoding='utf-8').read()
s2, n = re.subn(r'<g id="_窓とくま">.*?</g>\s*(?=<g id="窓">)', lambda _: grp, s, flags=re.S)
assert n == 1
open(svgp, 'w', encoding='utf-8').write(s2)
print('curves', len(plist), 'written')
