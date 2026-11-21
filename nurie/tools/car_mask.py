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
# 左耳（ライオン・ゾウ）を大きくして、右耳と同じ内がわの線を足す
import math
_lab,_n=ndimage.label(~keep)
F_l=_lab==_lab[120,300]; F_e=_lab==_lab[100,540]; M=_lab==_lab[100,400]   # ライオンの顔・ゾウの顔・たてがみの中
near=lambda r,k: ndimage.binary_dilation(r,iterations=k)
yy,xx=np.mgrid[0:H,0:W]
# ライオン左耳：頭の線の上の半円（中心_c、頭の線の向き_u、外向き_n）
_c=(239.5,87.0); _u=(0.755,-0.656); _n=(-0.656,-0.755)
keep[(np.hypot(xx-_c[0],yy-_c[1])<=21)&~near(F_l,5)]=False          # 前の小さな耳を消す
# ゾウ左耳：前の外がわの線を消す
_oc=(452,100); _rr=np.hypot(xx-_oc[0],yy-_oc[1])
keep[(_rr>=25)&(_rr<=41)&(yy<100)&~near(F_e,5)&~near(M,5)]=False
_layer=Image.new('L',(W,H),0); _d=ImageDraw.Draw(_layer)
def _semi(R,w): _d.line([(_c[0]+R*(math.cos(t)*_u[0]+math.sin(t)*_n[0]),_c[1]+R*(math.cos(t)*_u[1]+math.sin(t)*_n[1])) for t in [math.pi*i/32 for i in range(33)]],fill=255,width=w,joint='curve')
_semi(22,7); _semi(10,6)                                          # ライオン左耳：外がわと内がわ
keep|=ndimage.binary_closing(np.array(_layer)>0,iterations=2)&~F_l                                   # ライオンの耳はたてがみの上に描く（顔の中だけ隠す）
_layer=Image.new('L',(W,H),0); _d=ImageDraw.Draw(_layer)
_d.arc((_oc[0]-46,_oc[1]-46,_oc[0]+46,_oc[1]+46),150,330,fill=255,width=7)   # ゾウ左耳：外がわ（顔とたてがみのうしろは隠れる）
_d.arc((_oc[0]-28,_oc[1]-28,_oc[0]+28,_oc[1]+28),208,325,fill=255,width=7)   # ゾウ左耳：内がわ（下は開いたまま）
_L=ndimage.binary_closing(np.array(_layer)>0,iterations=2)   # 描いた線の中の白い点をうめる
keep|=_L&~F_l&~F_e&~M
# 小さな耳の中の白いすき間は、あとで線をならしてもつぶれないよう覚えておく
_h,_nh=ndimage.label(~keep); carve=np.zeros_like(keep)
for _i,_sl in enumerate(ndimage.find_objects(_h),1):
    if (_sl[1].start>=215 and _sl[1].stop<=262 and _sl[0].start>=60 and _sl[0].stop<=105) or (_sl[1].start>=418 and _sl[1].stop<=482 and _sl[0].start>=46 and _sl[0].stop<=175): carve|=_h==_i
np.save(sys.argv[2].replace('.npy','_carve.npy'),carve)
np.save(sys.argv[2],keep)
Image.fromarray(np.where(keep,0,255).astype('uint8')).save(sys.argv[2].replace('.npy','.png'))
