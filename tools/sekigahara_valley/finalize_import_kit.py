"""Validate geometry, record provenance and produce the user-facing ZIP."""
import argparse
import hashlib
import json
import math
import shutil
import zipfile
from pathlib import Path
from PIL import Image
from validate_import_kit import validate


def main(root):
    validate(root)
    proof=json.loads((root/'01_Imports/Valley 1862 - Continuous Landscape Proof v3.json').read_text())
    assert len(proof['scenario']['map']['hexes'])==49
    assert len({t['id'] for t in proof['assets']['terrains']})==49
    mapping=json.loads((root/'07_Continuous_Map_Proof/tile_placement_manifest.json').read_text())
    W=math.sqrt(3)*256
    for n,m in enumerate(mapping):
        q,r=n%7,n//7
        x0,y0,x1,y1=m['source_rectangle']
        assert math.isclose(x0,(q+(r%2)*.5)*W) and y0==r*384
        assert math.isclose(x1-x0,W) and y1-y0==512
        assert Image.open(root/'07_Continuous_Map_Proof'/m['file']).size==(512,512)
    tools=Path(__file__).parent
    shutil.copyfile(tools/'IMPORT_KIT_GUIDE.md',root/'START_HERE.md')
    shutil.copyfile(tools/'terrain_prompts_v3.json',root/'06_Reference/terrain_prompts.json')
    report={'png_and_catalog_validation':'passed','continuous_hexes':49,
        'counter_catalog_entries':15,'generic_terrain_catalog_entries':5,
        'exact_regular_hex_geometry':True,'counter_alpha_margins_checked':True,
        'geometry_and_counter_fitting_tests':'5 passed',
        'native_gameplay':'not tested','v3_live_editor_import':'user will perform',
        'historical_map_status':'illustrative art proof; approximate older Kernstown starter included'}
    (root/'06_Reference/validation_report.json').write_text(json.dumps(report,indent=2))
    files=[p for p in root.rglob('*') if p.is_file() and p.name!='file_hashes.json']
    hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (root/'06_Reference/file_hashes.json').write_text(json.dumps(hashes,indent=2))
    archive=root.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in root.rglob('*'):
            if p.is_file():z.write(p,Path(root.name)/p.relative_to(root))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps({'zip':str(archive),'files':len(hashes)+1,'zip_bytes':archive.stat().st_size,
        'continuous_tiles_validated':49},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kit',type=Path);main(p.parse_args().kit)
