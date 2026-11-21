import sys, numpy as np
from PIL import Image
from scipy import ndimage
X0,Y0,X1,Y1 = 660,460,1360,980
a = np.array(Image.open(sys.argv[1]).convert('L').crop((X0,Y0,X1,Y1))) < 128
H,W = a.shape
def hrun(b,y,x):
    l=x
    while l>0 and b[y,l-1]: l-=1
    r=x
    while r<W-1 and b[y,r+1]: r+=1
    return l,r
def vrun(b,y,x):
    t=y
    while t>0 and b[t-1,x]: t-=1
    d=y
    while d<H-1 and b[d+1,x]: d+=1
    return t,d
b=a.copy()
# 上の辺から下りる縦線を切る
for x in range(W):
    if b[0,x]:
        l,r=hrun(b,0,x)
        if r-l>12: continue
        y=0; cx=(l+r)//2
        while y<H and b[y,cx]:
            l,r=hrun(b,y,cx)
            if r-l>12: break
            b[y,l:r+1]=False; y+=1
# 左右の辺から入る横線を切る
for side in (0,W-1):
    for y in range(H):
        if b[y,side]:
            t,d=vrun(b,y,side)
            if d-t>12: continue
            x=side; cy=(t+d)//2; step=1 if side==0 else -1
            while 0<=x<W and b[cy,x]:
                t,d=vrun(b,cy,x)
                if d-t>12: break
                b[t:d+1,x]=False; x+=step
b[0:27,278:342]=False; b[192:214,651:]=False
# たてがみの上：メニュー板の角を消して平らになった山2つを、丸い山に描き直す
from PIL import ImageDraw
b[0:36,268:351]=False
_im=Image.fromarray(b.astype('uint8')*255); _d=ImageDraw.Draw(_im)
_d.arc((266,23,305,60),180,360,fill=255,width=7); _d.arc((304,24,350,61),180,360,fill=255,width=7)
b=np.array(_im)>0
lab,n=ndimage.label(b,structure=np.ones((3,3)))
sizes=ndimage.sum(b,lab,range(1,n+1)); big=int(np.argmax(sizes))+1
sil=ndimage.binary_fill_holes(lab==big)
keep=np.isin(lab,[i for i in range(1,n+1) if (sil&(lab==i)).sum()==(lab==i).sum()])
np.save(sys.argv[2].replace('.npy','_sil.npy'),sil)
# ハンドルを形に沿って黒くぬる：外側の丸い線（中心290,282・横40・縦46）の内がわにある白いすき間だけうめる（手の中は白のまま）
holes,nh=ndimage.label(~keep)
yy,xx=np.mgrid[0:H,0:W]; inside=((xx-290)/40.)**2+((yy-282)/46.)**2<=1
hands={holes[257,232],holes[260,348]}
for i in range(1,nh+1):
    if i in hands: continue
    m=holes==i; n=m.sum()
    if n<3000 and (m&inside).sum()>=0.9*n: keep[m]=True
# ハンドルの上と手のあいだの白いすき間は、あとで線をならしてもつぶれないよう少し広げて覚えておく
carve=np.zeros_like(keep)
for i in range(1,nh+1):
    sl=ndimage.find_objects(holes==i)[0]
    if i not in hands and sl[1].start>=240 and sl[1].stop<=345 and sl[0].start>=225 and sl[0].stop<=262 and not keep[holes==i].any():
        carve|=holes==i
carve=ndimage.binary_dilation(carve,iterations=1)
np.save(sys.argv[2].replace('.npy','_carve.npy'),carve)
np.save(sys.argv[2],keep)
Image.fromarray(np.where(keep,0,255).astype('uint8')).save(sys.argv[2].replace('.npy','.png'))
