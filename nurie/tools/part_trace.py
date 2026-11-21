# 使い方（一度きり）: <potracer+scipy入りのpython> nurie/tools/part_trace.py <参考画像.png> car|bush
# 参考画像（1536x1024）から部品だけを切り抜き（car → car_mask.py：車・ライオン・ゾウ、bush → bush_mask.py：手前の草2つ）、
# なぞってベクターにして、横版 illustrator/nurie-futsuu-yoko.svg の該当グループと入れ替える。
# ※ 2026-11-21 以降はユーザーがイラレで直すので、もう流さない（上書きになる）。
# 下に白い影（形の外がわ）を敷いて、うしろの地面や建物の線をかくす。
import os, re, sys, subprocess
import numpy as np, potrace
from PIL import Image
from scipy import ndimage
here = os.path.dirname(os.path.abspath(__file__)); svgp = os.path.join(os.path.dirname(here), 'illustrator', 'nurie-futsuu-yoko.svg')
PARTS = {  # マスク, 切り出し左上, 置き場所（参考画像の点 → ページの点）, 入れ替えるグループ（複数なら最初の場所に入れて残りは消す）
    'car':  ('car_mask.py',  (660, 460), ((683, 945), (376, 482)), ['_車と動物']),
    'bush': ('bush_mask.py', (158, 712), ((167, 950), (132, 500)), ['_植え込み', '_植え込み1']),
}
mask, (X0, Y0), ((rx, ry), (px, py)), gids = PARTS[sys.argv[2]]
tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), sys.argv[2] + 'mask.npy')
subprocess.run([sys.executable, os.path.join(here, mask), sys.argv[1], tmp], check=True)
keep = np.load(tmp); sil = ndimage.binary_fill_holes(keep | np.load(tmp.replace('.npy', '_sil.npy')))
UP = 3; K = 0.512
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
tx = px + (X0 - rx) * K; ty = py + (Y0 - ry) * K
grp = (f'<g id="{gids[0]}" transform="matrix({K/UP:.6f} 0 0 {K/UP:.6f} {tx:.2f} {ty:.2f})">\n'
       f'              <path id="白いかげ" style="fill:#fff;stroke:none" d="{"".join(dpath(c) for c in shadow)}" />\n'
       f'              <path id="線" style="fill:#111;fill-rule:evenodd;stroke:none" d="{"".join(dpath(c) for c in ink)}" />\n'
       f'            </g>')
s = open(svgp, encoding='utf-8').read()
def span(s, gid):
    i = s.index(f'<g id="{gid}"'); depth = 0
    for m in re.finditer(r'<g[\s>]|</g>', s[i:]):
        depth += 1 if m.group().startswith('<g') else -1
        if depth == 0: return i, i + m.end()
for k, gid in reversed(list(enumerate(gids))):
    i, j = span(s, gid)
    s = s[:i] + (grp if k == 0 else '') + s[j:]
open(svgp, 'w', encoding='utf-8').write(s)
print('ink', len(ink), 'shadow', len(shadow))
