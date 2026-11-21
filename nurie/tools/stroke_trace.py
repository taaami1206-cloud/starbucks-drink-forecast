# 使い方: <potracer+scipy+scikit-image入りのpython> nurie/tools/stroke_trace.py <参考画像.png> car|bush
# part_trace.py と同じ切り抜き（car_mask.py / bush_mask.py）から、
#   線 → 「線のまん中の通り道」を取り出してなめらかにし、一定の太さ（3.4）の線で描き直す
#   目・鼻など太い黒 → 塗りの形のまま（potraceでなぞる）
#   白いかげ → 外がわの形
# にして、横版 illustrator/nurie-futsuu-yoko.svg の該当グループと入れ替える。
# 手書きっぽいがたつき（線の太さのむら・波うち）がなくなる。
import os, re, sys, subprocess
import numpy as np, potrace
from PIL import Image, ImageFilter
from scipy import ndimage
from skimage.morphology import skeletonize, disk
here = os.path.dirname(os.path.abspath(__file__)); svgp = os.path.join(os.path.dirname(here), 'illustrator', 'nurie-futsuu-yoko.svg')
PARTS = {
    'car':  ('car_mask.py',  (660, 460), ((683, 945), (376, 482)), ['_車と動物']),
    'bush': ('bush_mask.py', (158, 712), ((167, 950), (132, 500)), ['_植え込み', '_植え込み1']),
}
mask, (X0, Y0), ((rx, ry), (px, py)), gids = PARTS[sys.argv[2]]
tmp = os.path.join(os.environ.get('TMPDIR', '/tmp'), sys.argv[2] + 'mask.npy')
subprocess.run([sys.executable, os.path.join(here, mask), sys.argv[1], tmp], check=True)
keep = np.load(tmp)
st = ndimage.iterate_structure(ndimage.generate_binary_structure(2, 1), 2)
keep = ndimage.binary_opening(ndimage.binary_closing(keep, st), st)
sil = ndimage.binary_fill_holes(keep | ndimage.binary_opening(np.load(tmp.replace('.npy', '_sil.npy')), st))
K = 0.512; SW = 3.4
tx = px + (X0 - rx) * K; ty = py + (Y0 - ry) * K

# 太い黒（目・鼻など）：線の太さ（約7px）より太いところ
parts, npart = ndimage.label(keep, np.ones((3, 3))); psz = ndimage.sum(keep, parts, range(1, npart + 1))
blob = np.isin(parts, [i + 1 for i in range(npart) if psz[i] < 3000])   # 目・鼻・口・しわなど、輪郭とつながっていない小さな部品は形のまま
PROTECT = {'car': [(200, 234, 382, 292)]}   # ハンドルと手のまわり（線が混みあって芯がうまく取れない）は前の形のまま
for x0, y0, x1, y1 in PROTECT.get(sys.argv[2], []):
    r = np.zeros_like(keep); r[y0:y1, x0:x1] = True; blob |= keep & r
lines = keep & ~blob

# ---- 線：芯を取り出してつなぐ ----
sk = skeletonize(lines)
H, W = sk.shape
nb = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
def neigh(y, x):
    return [(y + dy, x + dx) for dy, dx in nb if 0 <= y + dy < H and 0 <= x + dx < W and sk[y + dy, x + dx]]
deg = np.zeros_like(sk, dtype=int)
for y, x in zip(*np.nonzero(sk)): deg[y, x] = len(neigh(y, x))
nodes = set(zip(*np.nonzero(sk & (deg != 2))))
seen = set(); paths = []
def walk(start, nxt):
    path = [start, nxt]; seen.add(frozenset((start, nxt)))
    prev, cur = start, nxt
    while cur not in nodes:
        cand = [n for n in neigh(*cur) if n != prev and frozenset((cur, n)) not in seen]
        if not cand: break
        # まっすぐ隣（上下左右）を優先
        cand.sort(key=lambda n: abs(n[0] - cur[0]) + abs(n[1] - cur[1]))
        prev, cur = cur, cand[0]; seen.add(frozenset((prev, cur))); path.append(cur)
    return path
for n in nodes:
    for m in neigh(*n):
        if frozenset((n, m)) not in seen: paths.append((walk(n, m), False))
for y, x in zip(*np.nonzero(sk)):   # 枝分かれのない輪（目のまわり等）
    p = (y, x)
    if deg[y, x] == 2 and not any(frozenset((p, m)) in seen for m in neigh(*p)):
        path = walk(p, neigh(*p)[0]); paths.append((path, True))
# ひげ（短い行き止まり）を消す
def is_end(p): return p in nodes and deg[p] <= 1
paths = [(p, c) for p, c in paths if c or len(p) > 8 or not (is_end(p[0]) or is_end(p[-1]))]

def smooth(pts, closed, sigma=3.0):
    a = np.array(pts, float)
    if len(a) < 5: return a
    if closed:
        b = np.vstack([a[-20:], a, a[:20]]); b = ndimage.gaussian_filter1d(b, sigma, axis=0); return b[20:-20]
    b = ndimage.gaussian_filter1d(a, sigma, axis=0, mode='nearest'); b[0], b[-1] = a[0], a[-1]
    return b
def to_d(a, closed):
    a = a[::3] if len(a) > 6 else a
    if closed and len(a) > 2: a = np.vstack([a, a[:1]])
    pts = [(tx + x * K, ty + y * K) for y, x in a]
    if len(pts) < 3: return 'M' + ' L'.join(f'{x:.2f},{y:.2f}' for x, y in pts)
    s = f'M{pts[0][0]:.2f},{pts[0][1]:.2f}'
    for i in range(len(pts) - 1):   # Catmull-Rom → ベジェ
        p0 = pts[i - 1] if i > 0 else (pts[-2] if closed else pts[i]); p1 = pts[i]; p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else (pts[1] if closed else p2)
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        s += f'C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}'
    return s + ('Z' if closed else '')
stroke_d = ' '.join(to_d(smooth(p, c), c) for p, c in paths)

# ---- 塗り（太い黒）と白いかげ：potrace ----
UP = 3
def up(m, sigma):
    im = Image.fromarray(np.where(m, 0, 255).astype('uint8'))
    im = im.resize((im.width * UP, im.height * UP), Image.LANCZOS).filter(ImageFilter.GaussianBlur(sigma * UP))
    return np.array(im) >= 128
def dpath(c):
    s = f'M{c.start_point.x:.1f},{c.start_point.y:.1f}'
    for seg in c.segments:
        if seg.is_corner: s += f'L{seg.c.x:.1f},{seg.c.y:.1f}L{seg.end_point.x:.1f},{seg.end_point.y:.1f}'
        else: s += f'C{seg.c1.x:.1f},{seg.c1.y:.1f} {seg.c2.x:.1f},{seg.c2.y:.1f} {seg.end_point.x:.1f},{seg.end_point.y:.1f}'
    return s + 'Z'
tr = dict(turdsize=30, alphamax=1.1, opticurve=True, opttolerance=0.5)
shadow = potrace.Bitmap(up(sil, 2.0)).trace(**tr)
blobs = potrace.Bitmap(up(blob, 1.0)).trace(**tr) if blob.any() else []
m = f'matrix({K/UP:.6f} 0 0 {K/UP:.6f} {tx:.2f} {ty:.2f})'
grp = (f'<g id="{gids[0]}">\n'
       f'              <path id="白いかげ" transform="{m}" style="fill:#fff;stroke:none" d="{"".join(dpath(c) for c in shadow)}" />\n'
       + (f'              <path id="ぬり" transform="{m}" style="fill:#111;fill-rule:evenodd;stroke:none" d="{"".join(dpath(c) for c in blobs)}" />\n' if blobs else '')
       + f'              <path id="線" style="fill:none;stroke:#111;stroke-width:{SW:.2f}px;stroke-linecap:round;stroke-linejoin:round" d="{stroke_d}" />\n'
       f'            </g>')
s = open(svgp, encoding='utf-8').read()
def span(s, gid):
    i = s.index(f'<g id="{gid}"'); depth = 0
    for mm in re.finditer(r'<g[\s>]|</g>', s[i:]):
        depth += 1 if mm.group().startswith('<g') else -1
        if depth == 0: return i, i + mm.end()
for k, gid in reversed(list(enumerate(gids))):
    if k and f'<g id="{gid}"' not in s: continue
    i, j = span(s, gid); s = s[:i] + (grp if k == 0 else '') + s[j:]
open(svgp, 'w', encoding='utf-8').write(s)
print('strokes', len(paths), 'blobs', len(blobs), 'shadow', len(shadow))
