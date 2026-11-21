# 使い方: python3 nurie/tools/kantan.py
# illustrator/kantan-src.png（くまとうさぎの線画）から、かんたん版（A4横）を作る
# - 2倍に拡大して白黒2色にし、印刷で線がぼやけないようにする
# - 旗の「4」の中を黒くぬりつぶす（塗らなくていい数字にする）
# - 下に「なまえ」「さい」の欄をつける → illustrator/nurie-kantan2.svg
import os, io, base64
from PIL import Image, ImageDraw
here = os.path.dirname(os.path.abspath(__file__)); ill = os.path.join(os.path.dirname(here), 'illustrator')
g = Image.open(os.path.join(ill, 'kantan-src.png')).convert('L')
g = g.resize((g.width * 2, g.height * 2), Image.LANCZOS).point(lambda v: 0 if v < 150 else 255)
FOUR = (400, 660)                     # 「4」の太い部分の内側（2倍後の座標）
assert g.getpixel(FOUR) == 255
ImageDraw.floodfill(g, FOUR, 0)
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
