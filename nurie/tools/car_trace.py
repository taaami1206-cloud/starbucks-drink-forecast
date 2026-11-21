# 使い方（一度きり）: <potracer+scipy入りのpython> nurie/tools/car_trace.py <参考画像.png>
# 参考画像（1536x1024）から「車・ライオン・ゾウ」だけを切り抜き（car_mask.py と同じ処理）、
# なぞってベクターにして、横版 illustrator/nurie-futsuu-yoko.svg の <g id="_車と動物"> と入れ替える。
# 下に白い影（形の外がわ）を敷いて、うしろの地面や建物の線をかくす。
import os, re, sys, subprocess
import numpy as np, potrace
from PIL import Image
from scipy import ndimage
here = os.path.dirname(os.path.abspath(__file__)); svgp = os.path.join(os.path.dirname(here), 'illustrator', 'nurie-futsuu-yoko.svg')
tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), 'carmask.npy')
subprocess.run([sys.executable, os.path.join(here, 'car_mask.py'), sys.argv[1], tmp], check=True)
keep = np.load(tmp); sil = ndimage.binary_fill_holes(keep | np.load(tmp.replace('.npy', '_sil.npy')))
X0, Y0 = 660, 460; UP = 3; K = 0.512
def up(m):
    im = Image.fromarray(np.where(m, 0, 255).astype('uint8')).filter(__import__('PIL.ImageFilter', fromlist=['x']).GaussianBlur(0.6))
    return np.array(im.resize((im.width * UP, im.height * UP), Image.LANCZOS)) >= 128
def dpath(c):
    s = f'M{c.start_point.x:.1f},{c.start_point.y:.1f}'
    for seg in c.segments:
        if seg.is_corner: s += f'L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}'
        else: s += f'C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}'
    return s + 'Z'
ink = potrace.Bitmap(up(keep)).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.2)
shadow = potrace.Bitmap(up(sil)).trace(turdsize=60, alphamax=1.0, opticurve=True, opttolerance=0.2)
# 参考画像の座標 → ページ: x = 376 + (xr-683)*K, y = 482 + (yr-945)*K
tx = 376 + (X0 - 683) * K; ty = 482 + (Y0 - 945) * K
grp = (f'<g id="_車と動物" transform="matrix({K/UP:.6f} 0 0 {K/UP:.6f} {tx:.2f} {ty:.2f})">\n'
       f'              <path id="白いかげ" style="fill:#fff;stroke:none" d="{"".join(dpath(c) for c in shadow)}" />\n'
       f'              <path id="線" style="fill:#111;fill-rule:evenodd;stroke:none" d="{"".join(dpath(c) for c in ink)}" />\n'
       f'            </g>')
s = open(svgp, encoding='utf-8').read()
i = s.index('<g id="_車と動物"'); j = i; depth = 0
for m in re.finditer(r'<g[\s>]|</g>', s[i:]):
    depth += 1 if m.group().startswith('<g') else -1
    if depth == 0: j = i + m.end(); break
s = s[:i] + grp + s[j:]
open(svgp, 'w', encoding='utf-8').write(s)
print('ink', len(ink), 'shadow', len(shadow))
