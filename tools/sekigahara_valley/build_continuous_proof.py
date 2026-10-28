"""Cut full-bleed square editor textures from a single continuous landscape.

The square PNG is an intentional parameterization of a non-square hex bounding
box. The editor maps it onto that box. Never aspect-fit/crop the per-hex texture.
"""
import argparse
import copy
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw
from build_import_kit import uri,write_json,hex_points,font


def build(args):
    folder=args.kit/'07_Continuous_Map_Proof'
    tiles=folder/'Terrain_Uploads';tiles.mkdir(parents=True,exist_ok=True)
    master=Image.open(args.master).convert('RGB')
    master.save(folder/'Continuous_Landscape_Master.png')
    original=json.loads((args.kit/'01_Imports/Valley 1862 - Asset Fitting Board v2.json').read_text())
    data=copy.deepcopy(original)
    width,height=7,7
    # Keep irrational geometry in world coordinates; round only raster storage.
    R=256;W=math.sqrt(3)*R;pitch_y=3*R/2
    canvas_w=math.ceil((width+.5)*W);canvas_h=math.ceil((height-1)*pitch_y+2*R)
    world=master.resize((canvas_w,canvas_h),Image.Resampling.LANCZOS)
    grid=[];terrains=[];catalog=[];mapping=[]
    first=original['scenario']['map']['hexes'][0]
    preview=Image.new('RGB',world.size,'#e9e3d1')
    for r in range(height):
        for q in range(width):
            left=(q+(r%2)*.5)*W;top=r*pitch_y
            # Resizing, rather than cropping or contain, cancels the editor's
            # image-box transform and retains every part of the landscape crop.
            square=world.transform((512,512),Image.Transform.EXTENT,
                (left,top,left+W,top+2*R),resample=Image.Resampling.BICUBIC)
            kind='Woodland' if q<2 else 'Village' if (q,r)==(4,3) else 'Meadow'
            tid=f'vc1862_continuous_{q+1:02}_{r+1:02}'
            label=f'{kind} - joined map {q+1:02}{r+1:02}'
            filename=f'{tid}_512.png';square.save(tiles/filename,optimize=True)
            cost,defense=(2,2) if kind=='Woodland' else (1,2) if kind=='Village' else (1,1)
            terrains.append(dict(id=tid,label=label,type='image',imageUrl=uri(square),
                moveCost=cost,defenseMultiplier=defense,customId=1 if kind=='Woodland' else 3 if kind=='Village' else 0))
            internal=dict(category='terrain',id=tid,label=label,type='image',url=uri(square),
                moveCost=cost,combatMod=defense,customId=terrains[-1]['customId'])
            catalog.append(dict(id=tid,name=label,type='terrain',registeredAt=1793145600000,data=internal))
            h=copy.deepcopy(first);h.update(id=f'{q}-{r}',q=q,r=r,terrainId=tid,boxes=[0]*20,
                name='',isVPLocation=False,vp=dict(first=0,second=0),initialControl=None)
            if (q,r)==(4,3):h['name']=h['boxes'][9]='Hamlet - art fitting test'
            grid.append(h)
            restored=square.resize((math.ceil(W),2*R),Image.Resampling.LANCZOS)
            mask=Image.new('L',(math.ceil(W),2*R));ImageDraw.Draw(mask).polygon(hex_points(W/2,R,R),fill=255)
            preview.paste(restored,(round(left),round(top)),mask)
            mapping.append(dict(file='Terrain_Uploads/'+filename,hex=f'{q+1:02}{r+1:02}',
                label=label,source_rectangle=[left,top,left+W,top+2*R],source_canvas_size=[canvas_w,canvas_h]))
    data['assets']['terrains']=terrains
    data['scenario']['map']=dict(width=width,height=height,hexes=grid)
    data['scenario']['units']=[];data['assets']['unitTemplates']=[];data['assets']['images']={}
    name='Valley 1862 - Continuous Landscape Proof v3'
    data['scenario']['name']=data['meta']['scenarioName']=name
    data['meta']['description']={'en':'Illustrative 7 by 7 terrain fitting proof. One continuous generated landscape is cut across the point-top grid. '
        'No historical geography or order of battle is asserted. No units or objectives: this is an art board. '
        'Terrain costs are rough design regions, not surveyed vegetation coverage. '
        'Upload the exact square tiles without cropping; their bounding-box parameterization is intentional.'}
    write_json(args.kit/'01_Imports'/f'{name}.json',data)
    meta=dict(type='wargame_catalog',version=1,gameId='mustattack',exportedAt='2026-10-28T00:00:00Z')
    write_json(args.kit/'01_Imports/Valley_1862_Joined_Map_Terrain_Catalog_v3.json',dict(meta=meta,catalog=catalog))
    write_json(folder/'tile_placement_manifest.json',mapping)
    proof=preview.copy();draw=ImageDraw.Draw(proof)
    for h,m in zip(grid,mapping):
        left,top,_,_=m['source_rectangle'];points=hex_points(left+W/2,top+R,R)
        draw.line(points+[points[0]],fill='#c8bca0',width=2)
    preview.thumbnail((1600,1600));preview.save(args.kit/'05_Previews/Continuous_Landscape_No_Grid_v3.jpg',quality=95)
    proof.thumbnail((1600,1600));proof.save(args.kit/'05_Previews/Continuous_Landscape_With_Grid_v3.jpg',quality=95)
    print(json.dumps({'continuous_hexes':len(grid),'source_canvas_pixels':[canvas_w,canvas_h],
        'source_tile_bbox_pixels':[W,2*R],'upload_png_pixels':[512,512],
        'shared_source_for_every_tile':True},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--kit',type=Path,required=True)
    p.add_argument('--master',type=Path,required=True);build(p.parse_args())
