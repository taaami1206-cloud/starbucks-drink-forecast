# illustrator/ のSVGを index.html に埋め込む
#   nurie-kantan2.svg      → かんたん版（横） #easy
#   （ふつう版たて nurie-futsuu-nurie.svg は 2026-11-21 にページから外した：使うのは横の2枚だけ）
#   nurie-futsuu-yoko.svg  → ふつう版（横）   #yoko
# イラレのSVGはどれも .st0, .st1 … と同じクラス名・同じ clip のidを使うので、
# 同じページに並べてもぶつからないように、横版には目印（y）をつけて名前を変える。
import re, os
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
p = os.path.join(root, 'index.html'); html = open(p).read()

def load(name, prefix=''):
    svg = open(os.path.join(root, 'illustrator', name)).read()
    svg = svg[svg.index('<svg'):]
    svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S).replace('<svg ', '<svg class="art" ', 1).strip()
    if prefix:
        svg = re.sub(r'\.st(\d+)\b', rf'.{prefix}st\1', svg)
        svg = re.sub(r'class="([^"]*)"', lambda m: 'class="' + re.sub(r'\bst(\d+)\b', rf'{prefix}st\1', m.group(1)) + '"', svg)
        svg = re.sub(r'id="(clippath[^"]*)"', rf'id="{prefix}-\1"', svg)
        svg = re.sub(r'url\(#(clippath[^)]*)\)', rf'url(#{prefix}-\1)', svg)
    return svg

def put(html, sheet_id, svg):
    m = re.search(rf'<div class="sheet[^"]*" id="{sheet_id}">', html)
    start = m.end()
    end = html.index('</svg></div>', start) + len('</svg>')
    return html[:start] + svg + html[end:]

# かんたん版（A4横・くまとうさぎ）
if os.path.exists(os.path.join(root, 'illustrator', 'nurie-kantan2.svg')):
    html = html.replace('<div class="sheet" id="easy">', '<div class="sheet yoko" id="easy">')
    html = put(html, 'easy', load('nurie-kantan2.svg', 'k'))
if 'id="normal"' in html:
    html = put(html, 'normal', load('nurie-futsuu-nurie.svg'))
if os.path.exists(os.path.join(root, 'illustrator', 'nurie-futsuu-yoko.svg')):
    if 'id="yoko"' not in html:
        i = html.index('</svg></div>', html.index('id="normal"')) + len('</svg></div>')
        html = html[:i] + '\n<p class="label">ふつう版・横向き（幼稚園〜小学生むけ）</p>\n<div class="sheet yoko" id="yoko"><svg></svg></div>' + html[i:]
    html = put(html, 'yoko', load('nurie-futsuu-yoko.svg', 'y'))
open(p, 'w').write(html)
print('embedded')
