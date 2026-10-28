"""Build a local-only Sekigahara/Wargame Maker integration playtest.

No game binaries or synced reference files are changed. Pillow is required.
"""
import argparse
import base64
import copy
import hashlib
import io
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def encode(image):
    stream = io.BytesIO()
    image.save(stream, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(stream.getvalue()).decode()


def center(q, r, spacing=400):
    return (q + (r % 2) / 2) * spacing, r * math.sqrt(3) / 2 * spacing


def nearest(x, y, width, height):
    r0 = round(y / (400 * math.sqrt(3) / 2))
    choices = [(q, r) for r in range(max(0, r0 - 1), min(height, r0 + 2))
               for q in range(width)]
    return min(choices, key=lambda qr: sum((a-b)**2 for a,b in zip(center(*qr), (x,y))))


def neighbors(q, r):
    return ([(q+1,r),(q+1,r+1),(q,r+1),(q-1,r),(q,r-1),(q+1,r-1)] if r%2 else
            [(q+1,r),(q,r+1),(q-1,r+1),(q-1,r),(q-1,r-1),(q,r-1)])


def build(args):
    root, out = args.workspace, args.output
    out.mkdir(parents=True, exist_ok=True)
    layers = json.loads((root/'counter-design-work/data/layers/kernstown_hexes.json').read_text())
    roster = json.loads((root/'counter-design-work/data/layers/kernstown_units.json').read_text())
    sample = json.loads((args.game/'Scenarios/lCowpens1781.json').read_text(encoding='utf-8-sig'))
    art_path = root/'counter-design-work/previews/kernstown_full_nogrid.jpg'
    art = Image.open(art_path).convert('RGB')
    old = layers['grid']
    spacing = old['hex_yards'] * .9144
    xmax = (old['cols']-1) * spacing * math.sqrt(3)/2
    ymax = (old['rows']-.5) * spacing
    width, height = int(xmax//400)+1, int(ymax//(400*math.sqrt(3)/2))+1
    source = {(h['col'],h['row']):h for h in layers['hexes']}

    def old_xy(col,row):
        return col*spacing*math.sqrt(3)/2, ymax-(row+(col%2)/2)*spacing

    def old_at(x,y):
        c = min(old['cols']-1,max(0,round(x/(spacing*math.sqrt(3)/2))))
        r = min(old['rows']-1,max(0,round((ymax-y)/spacing-(c%2)/2)))
        return source[c,r]

    # One continuous image is sampled at world coordinates. Never rotate source
    # hex sprites: their flat-top masks do not match this engine's point-top grid.
    radius = 400/math.sqrt(3)
    terrain_rules = {'Plain':(1,1),'Road':(1,1),'Forest':(2,2),'Hill':(2,2),'Mountain':(4,3),
                     'River':(3,1),'Water':(4,1),'City':(1,2),'Town':(1,2)}
    hexes, terrains, counts = [], [], {}
    for r in range(height):
        for q in range(width):
            x,y = center(q,r)
            original = old_at(x,y)
            kind = original['type']
            counts[kind] = counts.get(kind,0)+1
            tid = f'valley_{q}_{r}'
            crop = art.transform((64,74),Image.Transform.EXTENT,
                ((x-200)/xmax*art.width,(y-radius)/ymax*art.height,
                 (x+200)/xmax*art.width,(y+radius)/ymax*art.height),
                resample=Image.Resampling.BICUBIC,fillcolor=(88,76,51))
            cost, defense = terrain_rules.get(kind,(2,1))
            terrains.append(dict(id=tid,label=f'{kind} {q+1:02}{r+1:02}',type='image',
                imageUrl=encode(crop),renderedUrl=None,moveCost=cost,defenseMultiplier=defense))
            h = copy.deepcopy(sample['scenario']['map']['hexes'][0])
            h.update(id=f'{q}-{r}',q=q,r=r,terrainId=tid,hasRiver=False,hasRoad=False,
                     rivers=[],roads=[],trails=[],majorRivers=[],fences=[],name='',
                     isVPLocation=False,vp={'first':0,'second':0},initialControl=None,boxes=[0]*20)
            hexes.append(h)
    units, templates, images = [], [], {}
    omitted = ['Hampden','Danville','Pleasants']
    # Exclude batteries flagged as unengaged/unverified in the existing review.
    for original in roster['units']:
        if any(word in original['custom_name'] for word in omitted):
            continue
        side = 0 if original['country']=='Union' else 1
        name = original['custom_name']
        artillery = original['template_name']=='Napoleon 12pdr'
        cavalry = original['template_name']=='Light Cavalry'
        strength = 2 if artillery or cavalry else (5 if side==0 else 4)
        movement, attack_range = (6 if cavalry else 4), (3 if artillery else 1)
        q,r = nearest(*old_xy(original['col'],original['row']),width,height)
        uid = len(units)+1
        boxes = [0]*20
        boxes[0:8] = [side,0,uid,'Union' if side==0 else 'Confederate',name,strength,movement,attack_range]
        u = copy.deepcopy(sample['scenario']['units'][0])
        u.update(id=uid,q=q,r=r,side=side,name=name,combatStrength=strength,
                 movePoints=movement,range=attack_range,boxes=boxes,templateId=f'local_{uid}')
        units.append(u)
        color = '#243c57' if side==0 else '#69685c'
        sprite = root/'output/counters/reference/civilhex/Land Units'/('Unit_CMN_Arty6lb.png' if artillery else
                 'Unit_CSA_Cav1.png' if cavalry else 'Unit_USA_Inf1.png' if side==0 else 'Unit_CSA_Inf1.png')
        shapes = [dict(type='rect',color=color,z=0,x=0,y=0,w=30,h=30,isRounded=False)]
        if sprite.exists():
            images[f'unit_{uid}']=encode(Image.open(sprite).convert('RGBA'))
            shapes.append(dict(type='image',z=1,x=0,y=-1,w=25,h=17,imageRef=f'unit_{uid}'))
        for z,(link,x,y,size) in enumerate([('box2',0,-11,5),('box5',-10,11,7),('box6',10,11,7)],2):
            shapes.append(dict(type='text',link=link,z=z,x=x,y=y,fontSize=size,color='#ffffff',
                               strokeColor='#000000',strokeWidth=.4))
        # Native runtime consumes renderedUrl as well as editable shapes.
        plate=Image.new('RGBA',(256,256),color)
        d=ImageDraw.Draw(plate)
        font=ImageFont.truetype('C:/Windows/Fonts/georgiab.ttf',38)
        if sprite.exists():
            pic=Image.open(sprite).convert('RGBA');pic.thumbnail((220,140));plate.alpha_composite(pic,((256-pic.width)//2,50))
        d.text((12,201),str(strength),font=font,fill='white')
        d.text((205,201),str(movement),font=font,fill='white')
        d.text((110,0),str(uid),font=font,fill='white')
        templates.append(dict(id=f'local_{uid}',name=name,isLocal=True,
                              visuals=dict(shapes=shapes,renderedUrl=encode(plate))))
    description = ('KERNSTOWN — ENGINE INTEGRATION PLAYTEST\n23 March 1862. '
        'Imported from our existing Valley Campaign map and approximate deployment. '
        '400 m between adjacent hex centers; 30 minutes per turn; 10 turns. '
        'Unit values, victory thresholds and deployments are provisional. '
        'Union is first side; Confederates move first. Hold or capture the marked objectives. '
        'Hampden, Danville and Pleasants batteries omitted pending historical roster review. '
        'Terrain art is resampled from our existing map preview, including its visual artifacts; '
        'terrain costs come from the source terrain classification. Painted roads and streams '
        'are visual only in this build. No 3D geometry, supply or command radius is implemented.')
    # Objectives use existing deployment anchors, not newly asserted farm coordinates.
    by={(h['q'],h['r']):h for h in hexes}
    for label,col,row,owner in [('Union position',25,26,0),('Confederate position',17,23,1)]:
        h=by[nearest(*old_xy(col,row),width,height)]
        h.update(name=label,isVPLocation=True,vp={'first':5,'second':5},initialControl=owner)
        h['boxes'][9:16]=[label,5,5,0,0,0,owner+1]
    rules=copy.deepcopy(sample['scenario']['rules'])
    rules.update(fix_rules=True,stacking_limit=2,zoc_exit_allowed=True,
                 activation_limit={'first':0,'second':0},standby_groups=[],night_turns=[])
    data=dict(meta=dict(version='2.0',scenarioName='Valley 1862 - Kernstown Playtest',gameId='mustattack',
            description={'en':description},descriptionDefaultLang='en',scaleMeters=400,scaleMinutes=30,
            scaleMen=None,briefingImage='',exportedAt='2026-10-28T00:00:00Z'),
        scenario=dict(name='Valley 1862 - Kernstown Playtest',sideNames=['Union','Confederacy'],
            firstMove='second',firstSideFlagRed=False,maxTurns=10,rules=rules,
            map=dict(width=width,height=height,hexes=hexes),units=units),
        victoryCondition=dict(winLine=0,tacticalThreshold=2,operationalThreshold=8,strategicThreshold=15),
        doctrine=dict(blue='def',red='off'),assets=dict(terrains=terrains,images=images,unitTemplates=templates))
    path=out/'Valley 1862 - Kernstown Playtest.json'
    path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    report=dict(hexes=len(hexes),units=len(units),dimensions=[width,height],terrain_counts=counts,
        scenario_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        source_art_sha256=hashlib.sha256(art_path.read_bytes()).hexdigest(),
        status='generated; requires editor and native gameplay verification',
        limitations=description)
    (out/'build-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='limitations'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--game',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    build(p.parse_args())
