"""Validate delivered PNG dimensions, fitting margins and catalog image references."""
import argparse
import base64
import io
import json
from pathlib import Path
from PIL import Image


def validate(root):
    data=json.loads((root/'01_Imports/Valley_1862_Complete_Catalog_v2.json').read_text(encoding='utf-8'))
    ids=[e['id'] for e in data['catalog']]
    assert len(ids)==len(set(ids))==20
    assert sum(e['type']=='terrain' for e in data['catalog'])==5
    checks=0
    for entry in data['catalog']:
        d=entry['data'];assert entry['name'] and d['label']
        if entry['type']=='terrain':
            im=Image.open(io.BytesIO(base64.b64decode(d['url'].split(',',1)[1])))
            assert im.size==(1024,1024);im.verify();checks+=1
        else:
            assert d['boxes'][3] and d['boxes'][4]
            assert {s.get('link') for s in d['shapes']} >= {'box3','box4','box5','box6','box7'}
            for s in d['shapes']:
                if s['type']=='image':
                    im=Image.open(io.BytesIO(base64.b64decode(s['url'].split(',',1)[1])))
                    assert im.size==(704,608) and im.mode=='RGBA'
                    assert im.width/im.height==s['w']/s['h']
                    x0,y0,x1,y1=im.getchannel('A').getbbox()
                    assert min(x0,y0,704-x1,608-y1)>=32
                    checks+=1
    for p in (root/'03_Counter_Uploads').glob('*.png'):
        assert Image.open(p).size==(512,512);checks+=1
    print(json.dumps({'status':'passed','catalog_entries':20,'images_checked':checks,
        'all_source_art_kept_inside_image_box':True},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kit',type=Path);validate(p.parse_args().kit)
