import sys, glob
from PIL import Image, ImageDraw
d,out,cols=sys.argv[1],sys.argv[2],int(sys.argv[3])
fs=sorted(glob.glob(d+'/*.png')); s=Image.open(fs[0]).size[0]
rows=(len(fs)+cols-1)//cols
W=Image.new('RGB',(s*cols,s*rows),'white')
for i,f in enumerate(fs):
    W.paste(Image.open(f).convert('RGB'),((i%cols)*s,(i//cols)*s)); ImageDraw.Draw(W).text(((i%cols)*s+5,(i//cols)*s+5),f.split('/')[-1][:-4],fill=(0,0,0))
W.save(out)
