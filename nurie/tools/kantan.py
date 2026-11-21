# 使い方: python3 nurie/tools/kantan.py
# illustrator/kantan-src.png（くまとうさぎの線画）から、かんたん版（A4横）を作る
# - 2倍に拡大して白黒2色にし、印刷で線がぼやけないようにする
# - 旗の「4」の中を黒くぬりつぶす（塗らなくていい数字にする）
# - 「4」は少し細くする／うさぎの耳の内側を下で閉じる／エプロンの丸を小さい黒丸にする
# - 下に「なまえ」「さい」の欄をつける → illustrator/nurie-kantan2.svg
import os, io, base64
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__)); ill = os.path.join(os.path.dirname(here), 'illustrator')
g = Image.open(os.path.join(ill, 'kantan-src.png')).convert('L')
g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS).point(lambda v: 0 if v < 150 else 255)
FOUR = (400, 660)                     # 「4」の太い部分の内側（2倍後の座標）
assert g.getpixel(FOUR) == 255
ImageDraw.floodfill(g, FOUR, 0)
# 「4」を少し細くする: 4だけを取り出して、まわりを削る
from PIL import ImageFilter
four = g.copy(); ImageDraw.floodfill(four, FOUR, 128)
mask = four.point(lambda v: 255 if v == 128 else 0)
THIN = 9                               # 削る幅（もとの画像で片側 9px ぶん）
thin = mask
for i in range(THIN * 2):              # 小さく何回も削る（角が丸くなる）
    thin = thin.filter(ImageFilter.MinFilter(3))
thin = thin.filter(ImageFilter.GaussianBlur(1.5)).point(lambda v: 255 if v > 128 else 0)  # ふちのギザギザをならす
g.paste(255, mask=mask); g.paste(0, mask=thin)
d = ImageDraw.Draw(g)
# うさぎの耳の内側の線を、下でU字につないで閉じる（もとの画像の座標 → 2倍）
def ucurve(p0, c, p1, w=9):
    pts = [((1-t)**2*p0[0] + 2*(1-t)*t*c[0] + t*t*p1[0], (1-t)**2*p0[1] + 2*(1-t)*t*c[1] + t*t*p1[1]) for t in [i/40 for i in range(41)]]
    pts = [(x*2, y*2) for x, y in pts]
    d.line(pts, fill=0, width=w*2, joint='curve')
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x-w, y-w, x+w, y+w], fill=0)
ucurve((1027, 280), (1048, 302), (1070, 264))
ucurve((1297, 283), (1302, 318), (1331, 309))
# エプロンの丸: 輪を消して、小さい黒丸にする
for cx, cy, r_old in [(624.5, 727, 76), (1126.5, 756, 71)]:
    R = (r_old + 4) * 2; d.ellipse([cx*2-R, cy*2-R, cx*2+R, cy*2+R], fill=255)
    r = 45 * 2; d.ellipse([cx*2-r, cy*2-r, cx*2+r, cy*2+r], fill=0)
g = g.convert('1'); g.save(os.path.join(ill, 'kantan-line.png'), optimize=True)
buf = io.BytesIO(); g.save(buf, 'PNG', optimize=True); b64 = base64.b64encode(buf.getvalue()).decode()

W, H = 841.9, 595.3
iw = 740; ih = iw * g.height / g.width; ix = (W - iw) / 2; iy = 18
FONT = "font-family:'M PLUS Rounded 1c','Hiragino Maru Gothic ProN',sans-serif;font-weight:800;font-size:19.8px;fill:#111"
BOX = 'fill:#fff;stroke:#111;stroke-width:3.4px;stroke-linejoin:round'
by = iy + ih + 14
svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="297mm" height="210mm">
  <g id="絵"><image x="{ix:.1f}" y="{iy}" width="{iw}" height="{ih:.1f}" xlink:href="data:image/png;base64,{b64}" href="data:image/png;base64,{b64}"/></g>
  <g id="名前と年齢">
    <rect id="名前欄" x="148" y="{by:.1f}" width="380" height="46" rx="13" style="{BOX}"/>
    <rect id="年齢欄" x="543" y="{by:.1f}" width="150" height="46" rx="13" style="{BOX}"/>
    <text x="166" y="{by+30:.1f}" style="{FONT}">なまえ</text>
    <text x="675" y="{by+30:.1f}" text-anchor="end" style="{FONT}">さい</text>
  </g>
</svg>
'''
open(os.path.join(ill, 'nurie-kantan2.svg'), 'w').write(svg)
print('image', round(ix), iy, iw, round(ih), 'boxes y', round(by), '-', round(by + 46))
