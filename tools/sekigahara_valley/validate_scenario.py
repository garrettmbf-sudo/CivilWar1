"""Check exported scenarios independently of the generator; no game-ready claim."""
import argparse
import base64
import collections
import io
import json
from pathlib import Path
from PIL import Image


def validate(path):
    d=json.loads(path.read_text(encoding='utf-8-sig'))
    s=d['scenario']; m=s['map']; a=d['assets']
    terrain={t['id']:t for t in a['terrains']}
    templates={t['id']:t for t in a['unitTemplates']}
    assert len(terrain)==len(a['terrains']), 'Duplicate terrain IDs'
    cells={(h['q'],h['r']):h for h in m['hexes']}
    assert len(cells)==m['width']*m['height']==len(m['hexes']), 'Incomplete/duplicate grid'
    assert set(cells)=={(q,r) for q in range(m['width']) for r in range(m['height'])}
    for h in cells.values():
        assert h['terrainId'] in terrain
        assert len(h['boxes'])==20
        assert h['name']==h['boxes'][9] or (not h['name'] and h['boxes'][9]==0)
        assert h['vp']['first']==h['boxes'][10] and h['vp']['second']==h['boxes'][11]
    occupied=collections.defaultdict(list)
    ids=set()
    for u in s['units']:
        assert u['id'] not in ids; ids.add(u['id'])
        assert (u['q'],u['r']) in cells and u['templateId'] in templates
        assert u['boxes'][0]==u['side'] and u['boxes'][2]==u['id']
        assert u['boxes'][5:8]==[u['combatStrength'],u['movePoints'],u['range']]
        occupied[u['q'],u['r']].append(u)
    for stack in occupied.values():
        assert len(stack)<=s['rules']['stacking_limit'], 'Stack exceeds native limit'
        assert len({u['side'] for u in stack})==1, 'Opposing units share a starting hex'
    for t in terrain.values():
        assert 1<=t['moveCost']<=5 and 1<=t['defenseMultiplier']<=3
        image=Image.open(io.BytesIO(base64.b64decode(t['imageUrl'].split(',',1)[1])))
        image.verify()
    for t in templates.values():
        for shape in t['visuals']['shapes']:
            if shape['type']=='image':
                assert shape['imageRef'] in a['images']
        assert t['visuals']['renderedUrl'].startswith('data:image/png;base64,')
    result={'hexes':len(cells),'units':len(ids),'terrain_images_decoded':len(terrain),
            'maximum_stack':max(map(len,occupied.values())),'status':'structural validation passed'}
    print(json.dumps(result,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('scenario',type=Path)
    validate(p.parse_args().scenario)
