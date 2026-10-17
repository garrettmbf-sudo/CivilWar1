"""Build review-only HoS PNGs. Never crop or modify approved portrait originals.

Run from any directory. Requires Pillow. No game installation is changed.
"""
from pathlib import Path
import csv, hashlib, json, math
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'design/miniatures'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def font(size):
    for path in ['C:/Windows/Fonts/georgiab.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf']:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)

def portrait_source(filename, root=ROOT):
    with (root / 'historical_data/portrait_manifest.csv').open(encoding='utf-8-sig', newline='') as f:
        entries = {r['filename']: r for r in csv.DictReader(f) if r.get('filename')}
    row = entries[filename]  # Unknown filenames must fail, never substitute another officer.
    if row['status'] == 'MISSING':
        return None
    if row['status'] != 'PRESENT' or row['audit_status'] != 'approved_existing':
        raise ValueError('Portrait not approved: ' + filename)
    source = root / row['github_path']
    if source.name != filename or not source.is_file():
        raise ValueError('Missing/mismatched approved source: ' + filename)
    return source

def compose(unit):
    image = Image.open(ART / 'masters' / (unit['key'] + '_blank.png')).convert('RGBA')
    source = portrait_source(unit['portrait'])
    if source:
        portrait = Image.open(source).convert('RGBA')
        x, y, radius = unit['medallion']
        # Fit the WHOLE original rectangle within the medallion circle. No crop,
        # face detection, masks, retouch, rank change, or identity replacement.
        ratio = 2 * radius / math.hypot(*portrait.size)
        portrait = portrait.resize((round(portrait.width * ratio), round(portrait.height * ratio)), Image.Resampling.LANCZOS)
        image.alpha_composite(portrait, (round(x - portrait.width / 2), round(y - portrait.height / 2)))
    x0,y0,x1,y1 = unit['nameplate']
    draw = ImageDraw.Draw(image)
    size = int((y1-y0)*.7)
    while draw.textbbox((0,0),unit['label'],font=font(size))[2] > x1-x0-12:
        size -= 1
    draw.text(((x0+x1)/2,(y0+y1)/2),unit['label'],font=font(size),fill='#30271d',anchor='mm')
    # Normalize generative native canvases to a common 2048px master. This is
    # resampling, not a claim that the generator provided 2048px native detail.
    master = Image.new('RGBA',(2048,2048))
    stand = ImageOps.contain(image,(1720,1720),Image.Resampling.LANCZOS)
    master.alpha_composite(stand,((2048-stand.width)//2,(2048-stand.height)//2))
    return master, source

def main():
    units = json.loads((ART/'asset_manifest.json').read_text())['units']
    records=[]
    for unit in units:
        master, source = compose(unit)
        master.save(ART/'masters'/(unit['key']+'_composited_2048.png'))
        for side in [1024,512]:
            folder=ART/'sprites'/str(side)/unit['country'];folder.mkdir(parents=True,exist_ok=True)
            master.resize((side,side),Image.Resampling.LANCZOS).save(folder/(unit['name']+'.png'))
        records.append({'id':unit['id'],'source':str(source.relative_to(ROOT)).replace('\\','/') if source else None,
                        'source_sha256':digest(source) if source else None,
                        'blank_sha256':digest(ART/'masters'/(unit['key']+'_blank.png')),
                        'sprite_sha256':digest(ART/'sprites/1024'/unit['country']/(unit['name']+'.png'))})
    (ART/'evidence/build_receipt.json').write_text(json.dumps(records,indent=2)+'\n')
    print('Built four 2048 masters and paired 1024/512 review PNGs; original portraits untouched.')

if __name__=='__main__':main()
