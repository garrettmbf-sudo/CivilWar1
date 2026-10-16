"""CivilWar1 lossless file-size study. No native game format changes.
For 2000 x 2000 tiles the supported in-game codec remains PNG.
WEBP/JPEG versions are reference/previews ONLY until the actual engine supports them.
"""
from pathlib import Path
from io import BytesIO
from PIL import Image
import zipfile,json,hashlib,time
import numpy as np
from skimage.metrics import structural_similarity
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'qa';OUT.mkdir(exist_ok=True)
SOURCES=[]
with zipfile.ZipFile('/mnt/data/civilhex.zip') as z:
 for n in ['civilhex/Plain.png','civilhex/River1.png','civilhex/Railroad1.png']:
  SOURCES.append((Path(n).stem+' (stock)',z.read(n)))
with zipfile.ZipFile('/mnt/data/CivilWar1_Valley_v4_Test_Kit.zip') as z:
 names=[n for n in z.namelist() if n.endswith('.png') and 'Graphics/Tiles' in n]
 for p in [names[0],next(n for n in names if '_M_' in n),next(n for n in names if '_H_' in n)]:
  SOURCES.append((Path(p).stem+' (v4)',z.read(p)))

for n in sorted((ROOT/'tiles_demo').glob('SV_CORRIDOR_*.png'))[:2]:
 SOURCES.append((n.stem+' (corridor-demo)',n.read_bytes()))

def pixels_same(a,b):
 x=np.asarray(a.convert('RGBA'));y=np.asarray(b.convert('RGBA'));return bool(np.array_equal(x,y))

def similarity(a,b):
 x=np.asarray(a.convert('RGB').resize((300,300)),np.uint8)
 y=np.asarray(b.convert('RGB').resize((300,300)),np.uint8)
 return float(structural_similarity(x,y,channel_axis=-1,data_range=255))

def png_variant(img,**kw):
 b=BytesIO();img.save(b,format='PNG',**kw);return b.getvalue()

results=[]
for name,buf in SOURCES:
 im=Image.open(BytesIO(buf));assert im.size==(2000,2000),(name,im.size)
 pix=im.convert('RGBA');rec={'tile':name,'dimensions':im.size,'input_mode':im.mode,'original_png_bytes':len(buf),'formats':{}}
 orig_id=hashlib.sha256(pix.tobytes()).hexdigest()
 baseline=png_variant(im,optimize=True,compress_level=9)
 lossless=pixels_same(im,Image.open(BytesIO(baseline)))
 rec['formats']['png_optimize_9']={'bytes':len(baseline),'ratio':round(len(baseline)/len(buf),4),'pixel_identical':lossless}
 # exact RGBA conversion often expands existing indexed files. Do not automatically force RGBA.
 conv=png_variant(pix,optimize=True,compress_level=9)
 rec['formats']['png_rgba_optimize']={'bytes':len(conv),'ratio':round(len(conv)/len(buf),4),'pixel_identical':pixels_same(im,Image.open(BytesIO(conv)))}
 web=BytesIO();pix.save(web,format='WEBP',lossless=True,method=6)
 bl=web.getvalue();rec['formats']['webp_lossless_ARCHIVE_ONLY']={'bytes':len(bl),'ratio':round(len(bl)/len(buf),4),'pixel_identical':pixels_same(im,Image.open(BytesIO(bl))),'engine_supported':False}
 # PIL quantization of painting can reduce tonal gradations: measure but do NOT ship by default.
 palette=pix.quantize(colors=256,method=Image.Quantize.FASTOCTREE,dither=Image.Dither.NONE)
 palb=png_variant(palette,optimize=True,compress_level=9)
 rec['formats']['png_palette256_OPTIONAL_REVIEW']={'bytes':len(palb),'ratio':round(len(palb)/len(buf),4),'pixel_identical':pixels_same(im,Image.open(BytesIO(palb))),'SSIM_300px':round(similarity(pix,palette),5)}
 results.append(rec)
 print(name, 'original',len(buf),'lossless PNG',len(baseline),'webp lossless',len(bl),'pal 256',len(palb),flush=True)
(OUT/'compression_benchmark.json').write_text(json.dumps(results,indent=2))
med=lambda data:round(float(np.median(data)),3)
summary={'count':len(results),'sample_type':'3 Hex of Steel stock PNGs, 3 CivilWar1 v4 PNGs, and 2 new proof-of-concept sprites; NOT from Kernstown release','all_2000px':True,'png_lossless_median_ratio':med([r['formats']['png_optimize_9']['ratio'] for r in results]),'webp_lossless_median_ratio':med([r['formats']['webp_lossless_ARCHIVE_ONLY']['ratio'] for r in results]),'palette256_median_ratio':med([r['formats']['png_palette256_OPTIONAL_REVIEW']['ratio'] for r in results]),'palette256_min_SSIM':min(r['formats']['png_palette256_OPTIONAL_REVIEW']['SSIM_300px'] for r in results),'png_identical':all(r['formats']['png_optimize_9']['pixel_identical'] for r in results)}
(OUT/'compression_summary.json').write_text(json.dumps(summary,indent=2));print(summary)