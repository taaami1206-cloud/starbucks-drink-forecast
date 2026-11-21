# illustrator/nurie-futsuu-nurie.svg を index.html の「ふつう版」に埋め込む
import re, os
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(here)
svg = open(os.path.join(root, 'illustrator', 'nurie-futsuu-nurie.svg')).read()
svg = svg[svg.index('<svg'):]
svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S).replace('<svg ', '<svg class="art" ', 1).strip()
p = os.path.join(root, 'index.html'); html = open(p).read()
start = html.index('<div class="sheet" id="normal">') + len('<div class="sheet" id="normal">')
end = html.index('</svg></div>', start) + len('</svg>')
open(p, 'w').write(html[:start] + svg + html[end:])
print('embedded', len(svg))
