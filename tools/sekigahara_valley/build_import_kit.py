"""Named editor catalogue, upload PNGs, and a clean terrain scenario.

Image fitting/packaging is deterministic; generated terrain masters are inputs.
Original sprites and portraits are never changed.
"""
import argparse
import base64
import copy
import csv
import hashlib
import io
import json
import math
import re
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONTS=Path('C:/Windows/Fonts')


def font(size):
    return ImageFont.truetype(str(FONTS/'georgiab.ttf'),size)


def uri(image):
    b=io.BytesIO();image.save(b,format='PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode()


def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')


def slug(text):
    return re.sub('[^A-Za-z0-9]+','_',text).strip('_')


def fit_art(path):
    original=Image.open(path).convert('RGBA')
    bbox=original.getchannel('A').getbbox()
    assert bbox,'Empty source artwork'
    # Trim transparent padding only, preserving every nontransparent source pixel.
    subject=original.crop(bbox)
    subject=ImageOps.contain(subject,(576,480),method=Image.Resampling.LANCZOS)
    fitted=Image.new('RGBA',(704,608))
    x,y=(704-subject.width)//2,(608-subject.height)//2
    fitted.alpha_composite(subject,(x,y))
    bounds=fitted.getchannel('A').getbbox()
    assert bounds[0]>=32 and bounds[1]>=32 and bounds[2]<=672 and bounds[3]<=576
    return fitted,{'original_size':list(original.size),'original_alpha_bbox':list(bbox),
                   'upload_size':[704,608],'fitted_alpha_bbox':list(bounds)}


def hex_points(cx,cy,radius):
    return [(cx+math.cos(math.radians(60*k-30))*radius,
             cy+math.sin(math.radians(60*k-30))*radius) for k in range(6)]


def render_counter(u,art,title,formation):
    color='#243e58' if u['side']==0 else '#656458'
    result=Image.new('RGBA',(512,512),color)
    d=ImageDraw.Draw(result)
    d.rectangle((4,4,507,507),outline='#d0c5a0',width=5)
    d.rectangle((13,13,498,104),fill='#182a3d' if u['side']==0 else '#46483f')
    for text,y,initial in [(title,20,37),(formation,65,24)]:
        size=initial
        while d.textbbox((0,0),text,font=font(size))[2]>460 and size>10:size-=1
        d.text((256,y),text,font=font(size),anchor='mt',fill='#faf3da')
    # Same 22:19 box as editable shapes. Art cannot touch the header or values.
    pic=art.resize((352,304),Image.Resampling.LANCZOS)
    result.alpha_composite(pic,(80,104))
    for value,x in [(u['combatStrength'],51),(u['movePoints'],461)]:
        d.text((x,442),str(value),anchor='mm',font=font(64),fill='white')
    d.text((256,448),f'R{u["range"]}',anchor='mm',font=font(28),fill='#e9dfbe')
    return result


def main(args):
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    for folder in ['01_Imports','02_Terrain_Uploads','03_Counter_Uploads','04_Unit_Art','05_Previews','06_Reference']:
        (out/folder).mkdir(exist_ok=True)
    scenario=json.loads(args.scenario.read_text(encoding='utf-8-sig'))
    old_terrains={t['id']:t for t in scenario['assets']['terrains']}
    definitions=[('meadow','Valley Meadow',0,1,1),('woodland','Valley Woodland',1,2,2),
                 ('ridge','Valley High Ground',4,2,2),('village','Valley Village',3,1,2)]
    terrain_images={};terrain_entries=[];catalog=[];manifest=[]
    for key,label,custom,cost,defense in definitions:
        master=args.masters/f'{key}.png'
        image=ImageOps.fit(Image.open(master).convert('RGB'),(1024,1024),method=Image.Resampling.LANCZOS)
        tid='valley_'+key
        filename=f'{tid}_1024.png';image.save(out/'02_Terrain_Uploads'/filename,optimize=True)
        terrain_images[tid]=image
        data=dict(category='terrain',id=tid,label=label,type='image',customId=custom,
                  url=uri(image),moveCost=cost,combatMod=defense)
        terrain_entries.append(dict(id=tid,label=label,type='image',customId=custom,
                 imageUrl=data['url'],renderedUrl=None,moveCost=cost,defenseMultiplier=defense))
        catalog.append(dict(id='vc1862_v2_terrain_'+key,name=label,type='terrain',registeredAt=1793145600000,data=data))
        manifest.append(dict(file='02_Terrain_Uploads/'+filename,label=label,kind='terrain',
                              width=1024,height=1024,movement=cost,defence=defense))
    # Retain river cells as a clearly named provisional fordable channel, rather
    # than silently turning them into grass. Native river edges are still manual.
    channel=ImageOps.fit(Image.open(args.masters/'channel.png').convert('RGB'),(1024,1024),method=Image.Resampling.LANCZOS)
    channel.save(out/'02_Terrain_Uploads/valley_channel_1024.png')
    terrain_images['valley_channel']=channel
    channel_data=dict(category='terrain',id='valley_channel',label='Valley Channel - provisional crossing',
        type='image',customId=6,url=uri(channel),moveCost=3,combatMod=1)
    catalog.append(dict(id='vc1862_v2_terrain_channel',name=channel_data['label'],type='terrain',registeredAt=1793145600000,data=channel_data))
    terrain_entries.append(dict(id='valley_channel',label=channel_data['label'],type='image',customId=6,
        imageUrl=channel_data['url'],renderedUrl=None,moveCost=3,defenseMultiplier=1))
    manifest.append(dict(file='02_Terrain_Uploads/valley_channel_1024.png',label=channel_data['label'],kind='terrain',width=1024,height=1024,movement=3,defence=1))
    kinds={'Plain':'meadow','Road':'meadow','Forest':'woodland','Hill':'ridge','Mountain':'ridge',
           'City':'village','Town':'village','River':'channel','Water':'channel'}
    for h in scenario['scenario']['map']['hexes']:
        old=old_terrains[h['terrainId']]
        kind=old.get('label',old.get('name','Plain')).split()[0]
        h['terrainId']='valley_'+kinds[kind]
    # Names distinguish formation identity from source sprite or numeric unit ID.
    labels=[('GARNETT','STONEWALL BRIGADE'),('FULKERSON','VIRGINIA BRIGADE'),('BURKS','VIRGINIA BRIGADE'),
            ('ASHBY','VIRGINIA CAVALRY'),('CHEW','HORSE ARTILLERY'),('POAGUE','ROCKBRIDGE BATTERY'),
            ('CARPENTER','ALLEGHANY BATTERY'),('KIMBALL','1ST BRIGADE'),('SULLIVAN','2ND BRIGADE'),
            ('TYLER','3RD BRIGADE'),('JENKS','VIRGINIA BATTERY'),('BATTERY B','VIRGINIA ARTILLERY'),
            ('CLARK','4TH U.S. ARTILLERY'),('ROBINSON','1ST OHIO ARTILLERY'),('BRODHEAD','UNION CAVALRY')]
    art_cache={};templates=[];image_assets={};normalization=[]
    for u,(title,formation) in zip(scenario['scenario']['units'],labels,strict=True):
        side='USA' if u['side']==0 else 'CSA'
        kind='Artillery' if u['range']>1 else 'Cavalry' if u['movePoints']>4 else 'Infantry'
        source_name='Unit_CMN_Arty6lb.png' if kind=='Artillery' else f'Unit_{side}_Cav1.png' if kind=='Cavalry' else f'Unit_{side}_Inf1.png'
        if source_name not in art_cache:
            art,record=fit_art(Path(__file__).resolve().parents[2]/'units'/source_name)
            art_cache[source_name]=art;record['source']=source_name;normalization.append(record)
        art=art_cache[source_name]
        stem=f'{side}_{slug(title.title())}_{slug(formation.title())}'
        art.save(out/'04_Unit_Art'/f'{stem}_art_704x608.png')
        plate=render_counter(u,art,title,formation)
        plate.save(out/'03_Counter_Uploads'/f'{stem}_counter_512.png')
        u['name']=f'{title.title()} - {formation.title()}'
        u['boxes'][3:5]=[title,formation]
        color='#243e58' if u['side']==0 else '#656458'
        image_id='vc1862_art_'+str(u['id']); image_assets[image_id]=uri(art)
        shapes=[dict(type='rect',x=0,y=0,w=30,h=30,z=0,color=color,strokeColor='#d0c5a0',strokeWidth=.3),
                dict(type='rect',x=0,y=-11.5,w=29,h=6,z=1,color='#182a3d' if u['side']==0 else '#46483f'),
                dict(type='image',x=0,y=0,w=22,h=19,z=2,imageRef=image_id)]
        for z,(link,x,y,size) in enumerate([('box3',0,-12.4,2.0),('box4',0,-9.7,1.35),
                 ('box5',-11,11.2,4),('box6',11,11.2,4),('box7',0,12.0,1.8)],3):
            shapes.append(dict(type='text',link=link,x=x,y=y,z=z,fontSize=size,color='#ffffff',
                               fontFamily='Georgia',fontWeight=700,strokeWidth=.08,strokeColor='#000000'))
        templates.append(dict(id=u['templateId'],name=u['name'],isLocal=True,
                        visuals=dict(shapes=shapes,renderedUrl=uri(plate))))
        cat_shapes=copy.deepcopy(shapes)
        cat_shapes[2]['url']=image_assets[image_id];del cat_shapes[2]['imageRef']
        catalog.append(dict(id='vc1862_v2_'+stem,name=f'{side} {u["name"]}',type='unit',
            registeredAt=1793145600000,data=dict(category='unit',label=f'{side} {u["name"]}',
                boxes=u['boxes'],shapes=cat_shapes)))
        manifest.append(dict(file=f'03_Counter_Uploads/{stem}_counter_512.png',label=u['name'],kind=kind,
            width=512,height=512,art_file=f'04_Unit_Art/{stem}_art_704x608.png',side=side))
    scenario['assets']=dict(terrains=terrain_entries,images=image_assets,unitTemplates=templates)
    name='Valley 1862 - Kernstown Import Kit v2'
    scenario['meta']['scenarioName']=scenario['scenario']['name']=name
    scenario['meta']['description']={'en':'Kernstown editor construction starter. Clean terrain library and fully fitted named counters. '
        'Inherited deployment and terrain classification are approximate. Terrain art is illustrative. '
        'Road and river edge connections require manual tracing; river cells are provisionally fordable at cost 3. '
        'Unit statistics and objectives are provisional. No true 3D elevation, supply or command-radius system is implemented. '
        'These are local review assets; existing sprite redistribution rights remain unverified.'}
    write_json(out/'01_Imports'/f'{name}.json',scenario)
    meta=dict(type='wargame_catalog',version=1,gameId='mustattack',exportedAt='2026-10-28T00:00:00Z')
    for filename,entries in [('Valley_1862_Complete_Catalog_v2.json',catalog),
        ('Valley_1862_Terrain_Catalog_v2.json',[e for e in catalog if e['type']=='terrain']),
        ('Valley_1862_Unit_Catalog_v2.json',[e for e in catalog if e['type']=='unit'])]:
        write_json(out/'01_Imports'/filename,dict(meta=meta,catalog=entries))
    # A separate demonstration board tests six shared edges and counter fit.
    demo=copy.deepcopy(scenario);demo['scenario']['map']=dict(width=9,height=9,hexes=[])
    first=copy.deepcopy(scenario['scenario']['map']['hexes'][0])
    for r in range(9):
        for q in range(9):
            h=copy.deepcopy(first);h.update(id=f'{q}-{r}',q=q,r=r,name='',boxes=[0]*20,
                terrainId=['valley_meadow','valley_woodland','valley_ridge','valley_village'][min(3,q//3)],
                isVPLocation=False,vp=dict(first=0,second=0),initialControl=None)
            demo['scenario']['map']['hexes'].append(h)
    for index,u in enumerate(demo['scenario']['units']):u['q'],u['r']=1+index%5,2+index//5*2
    demo_name='Valley 1862 - Asset Fitting Board v2'
    demo['scenario']['name']=demo['meta']['scenarioName']=demo_name
    write_json(out/'01_Imports'/f'{demo_name}.json',demo)
    write_json(out/'06_Reference/asset_manifest.json',manifest)
    write_json(out/'06_Reference/counter_fit_validation.json',normalization)
    with (out/'06_Reference/hex_settings.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=['hex_coordinate','place_name','vp_union','vp_confederacy','cp_union','cp_confederacy','initial_control','status']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for h in scenario['scenario']['map']['hexes']:
            if h['name']:
                writer.writerow(dict(hex_coordinate=f'{h["q"]+1:02}{h["r"]+1:02}',place_name=h['name'],
                    vp_union=h['vp']['first'],vp_confederacy=h['vp']['second'],cp_union=0,cp_confederacy=0,
                    initial_control=['Union','Confederacy'][h['initialControl']],status='Provisional position objective; not a researched place name'))
    with (out/'06_Reference/unit_registry.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['unit_name','side_B0','commander_B3','formation_B4','strength_B5','movement_B6','range_B7','hex_coordinate','status'])
        for u in scenario['scenario']['units']:
            writer.writerow([u['name'],u['side'],*u['boxes'][3:8],f'{u["q"]+1:02}{u["r"]+1:02}','Inherited approximate deployment; playtest values'])
    # Contact sheet shows opaque complete counters and actual point-top masks.
    sheet=Image.new('RGB',(1600,1500),'#eee7d6');d=ImageDraw.Draw(sheet)
    d.text((40,25),'VALLEY 1862 | EDITOR IMPORT KIT',font=font(36),fill='#243e58')
    for n,(tid,image) in enumerate(terrain_images.items()):
        x=50+n*300; mask=Image.new('L',(240,278));md=ImageDraw.Draw(mask)
        md.polygon(hex_points(120,139,138),fill=255)
        tile=ImageOps.fit(image,(240,278),method=Image.Resampling.LANCZOS)
        sheet.paste(tile,(x,100),mask)
        d.text((x,390),tid.replace('valley_','').upper(),font=font(19),fill='#243e58')
    counters=[m for m in manifest if m['kind']!='terrain']
    for n,item in enumerate(counters):
        x=40+(n%5)*310;y=460+(n//5)*330
        pic=Image.open(out/item['file']).convert('RGB').resize((240,240),Image.Resampling.LANCZOS)
        sheet.paste(pic,(x,y));d.text((x,y+250),item['label'].split(' - ')[0],font=font(19),fill='#243e58')
    sheet.save(out/'05_Previews/Valley_1862_Asset_Reference.jpg',quality=94)
    # Point-top board proof: no old map screenshot or baked second grid.
    R=80;preview=Image.new('RGB',(1400,1350),'#eee7d6')
    for h in demo['scenario']['map']['hexes']:
        cx=100+(h['q']+(h['r']%2)/2)*math.sqrt(3)*R;cy=100+h['r']*1.5*R
        mask=Image.new('L',(140,162));ImageDraw.Draw(mask).polygon(hex_points(70,81,R),fill=255)
        im=ImageOps.fit(terrain_images[h['terrainId']],(140,162))
        preview.paste(im,(round(cx-70),round(cy-81)),mask)
        ImageDraw.Draw(preview).line(hex_points(cx,cy,R)+[hex_points(cx,cy,R)[0]],fill='#968b69',width=1)
    preview.save(out/'05_Previews/Point_Top_Hex_Geometry.jpg',quality=94)
    hashes={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
    write_json(out/'06_Reference/file_hashes.json',hashes)
    print(json.dumps(dict(terrains=len(terrain_entries),named_counters=len(templates),catalog_entries=len(catalog),
        source_subjects_fitted=len(normalization),output=str(out)),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--scenario',type=Path,required=True);p.add_argument('--masters',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
