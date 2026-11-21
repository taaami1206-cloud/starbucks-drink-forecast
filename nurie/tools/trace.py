# 使い方: <potracer入りのpython> nurie/tools/trace.py
#   （必要なもの: pip install potracer numpy pillow）
# illustrator/kantan-line.png（白黒の線画）をなぞってベクター（図形）にし、
# かんたん版 illustrator/nurie-kantan2.svg を「イラレで編集できる」形で作り直す。
# 線のかたまりごとに別の <path>（穴は同じ path の中で抜く）にするので、1つずつ選んで直せる。
import os, re, time
import numpy as np, potrace
from PIL import Image
here = os.path.dirname(os.path.abspath(__file__)); ill = os.path.join(os.path.dirname(here), 'illustrator')
im = Image.open(os.path.join(ill, 'kantan-line.png')).convert('L')
bm = potrace.Bitmap(np.array(im) >= 128)   # potracer は False のところ（＝黒）をなぞる
t0 = time.time()
plist = bm.trace(turdsize=8, alphamax=1.0, opticurve=True, opttolerance=0.2)
print('traced', len(plist), 'curves in', round(time.time() - t0, 1), 's')

def dpath(c):
    s = f'M{c.start_point.x:.1f},{c.start_point.y:.1f}'
    for seg in c.segments:
        if seg.is_corner:
            s += f'L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}'
        else:
            s += f'C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}'
    return s + 'Z'
def poly(c):
    pts = [(c.start_point.x, c.start_point.y)]
    for seg in c.segments:
        pts.append((seg.end_point.x, seg.end_point.y))
    return pts
def area(p):
    return 0.5 * sum(p[i][0] * p[i-1][1] - p[i-1][0] * p[i][1] for i in range(len(p)))
def inside(pt, p):
    x, y = pt; c = False
    for i in range(len(p)):
        x1, y1 = p[i]; x2, y2 = p[i-1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
polys = [poly(c) for c in plist]
bbox = [(min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)) for p in polys]
# 入れ子の深さ（偶数=黒い形の外がわ、奇数=穴）を数え、穴をすぐ外がわの形にまとめる
order = sorted(range(len(polys)), key=lambda i: abs(area(polys[i])), reverse=True)
parent = {}
for k, i in enumerate(order):
    best = None
    for j in order[:k]:
        bj, bi = bbox[j], bbox[i]
        if bj[0] <= bi[0] and bj[1] <= bi[1] and bj[2] >= bi[2] and bj[3] >= bi[3] and inside(polys[i][0], polys[j]):
            best = j  # 面積の大きい順なので、最後に見つかったものがいちばん近い外がわ
    parent[i] = best
def depth(i):
    d = 0
    while parent[i] is not None: i = parent[i]; d += 1
    return d
groups = {}
for i in range(len(polys)):
    if depth(i) % 2 == 0: groups.setdefault(i, [i])
    else: groups.setdefault(parent[i], [parent[i]]).append(i)
print('shapes', len(groups))

# 置き場所は今のかんたん版と同じ（画像の位置・大きさを引きつぐ）
old = open(os.path.join(ill, 'nurie-kantan2.svg')).read()
m = re.search(r'<image x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', old)
ix, iy, iw, ih = map(float, m.groups()); k = iw / im.width
paths = '\n'.join(f'    <path d="{"".join(dpath(plist[j]) for j in g)}"/>' for g in groups.values())
art = f'''  <g id="絵" transform="matrix({k:.6f} 0 0 {k:.6f} {ix:.2f} {iy:.2f})" style="fill:#111;fill-rule:evenodd;stroke:none">
{paths}
  </g>'''
new = re.sub(r'  <g id="絵">.*?</g>', lambda _: art, old, flags=re.S)
new = new.replace('xmlns:xlink="http://www.w3.org/1999/xlink" ', '')
open(os.path.join(ill, 'nurie-kantan2.svg'), 'w').write(new)
print('written', len(new) // 1024, 'KB')
