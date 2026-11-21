import re, sys, xml.etree.ElementTree as ET
NS='http://www.w3.org/2000/svg'
def path_pts(d):
    toks=re.findall(r'[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d)
    pts=[]; i=0; cx=cy=sx=sy=0; cmd=None
    def num():
        nonlocal i; v=float(toks[i]); i+=1; return v
    while i<len(toks):
        if re.match(r'[A-Za-z]',toks[i]): cmd=toks[i]; i+=1
        if cmd in 'Zz': cx,cy=sx,sy; continue
        rel=cmd.islower(); C=cmd.upper()
        ox,oy=(cx,cy) if rel else (0,0)
        if C=='M': cx,cy=ox+num(),oy+num(); sx,sy=cx,cy; pts.append((cx,cy)); cmd='l' if rel else 'L'
        elif C=='L' or C=='T': cx,cy=ox+num(),oy+num(); pts.append((cx,cy))
        elif C=='H': cx=(cx if rel else 0)+num(); pts.append((cx,cy))
        elif C=='V': cy=(cy if rel else 0)+num(); pts.append((cx,cy))
        elif C=='C':
            for _ in range(3): x,y=ox+num(),oy+num(); pts.append((x,y))
            cx,cy=x,y
        elif C in 'SQ':
            for _ in range(2): x,y=ox+num(),oy+num(); pts.append((x,y))
            cx,cy=x,y
        elif C=='A':
            num();num();num();num();num(); cx,cy=ox+num(),oy+num(); pts.append((cx,cy))
    return pts
def bbox(el):
    t=el.tag.split('}')[-1]; g=lambda k: float(el.get(k,0))
    if t=='path': p=path_pts(el.get('d'))
    elif t in('polygon','polyline'):
        n=list(map(float,re.findall(r'-?[\d.]+',el.get('points')))); p=list(zip(n[::2],n[1::2]))
    elif t=='circle': r=g('r'); p=[(g('cx')-r,g('cy')-r),(g('cx')+r,g('cy')+r)]
    elif t=='ellipse': p=[(g('cx')-g('rx'),g('cy')-g('ry')),(g('cx')+g('rx'),g('cy')+g('ry'))]
    elif t=='rect': p=[(g('x'),g('y')),(g('x')+g('width'),g('y')+g('height'))]
    elif t=='line': p=[(g('x1'),g('y1')),(g('x2'),g('y2'))]
    else: return None
    if not p: return None
    xs=[a for a,b in p]; ys=[b for a,b in p]; return min(xs),min(ys),max(xs),max(ys)
