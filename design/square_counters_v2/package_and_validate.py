"""Validate deliverables and package only new counter output, never installed art."""
from pathlib import Path
import hashlib,json,shutil,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parent
REPO=Path('C:/Users/garre/.codex/.chatgpt-projects/g-p-6ad11f6471d8819184b9b19af1b48218/kernstown-miniatures')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    roster=json.loads((ROOT/'roster_manifest.json').read_text(encoding='utf-8'))['units']
    rows=[]
    for u in roster:
        p=ROOT/u['install_path']
        im=Image.open(p)
        assert im.size==(1024,1024) and im.mode=='RGBA'
        assert im.getpixel((0,0))[3]==0
        assert im.getchannel('A').getextrema()==(0,255)
        svg=(ROOT/'masters'/u['country']/(u['name']+'.svg')).read_text(encoding='utf-8')
        assert '<ellipse' not in svg and u['portrait'] is None
        assert len([s for s in svg.split('data:image/png;base64,')])-1==1
        rows.append({'name':u['name'],'sha256':sha(p),'size':im.size,'portrait_present':False})
    assert len(rows)==18 and len({r['sha256'] for r in rows})==18
    assert sum(u['country']=='Confederacy' for u in roster)==10
    assert sum(u['country']=='Union' for u in roster)==8
    receipt={'units':rows,'png_count':18,'unique_hashes':18,'portrait_inserts':0,
             'formation_source_sha256':sha(ROOT/'source/formation_sheet.png'),
             'game_tested':False,'original_portraits_modified':False,
             'installed_mod_modified':False,'historical_roster_authority':'User supplied'}
    (ROOT/'package_validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    # Exclude earlier unused portrait working copies and all caches from delivery.
    files=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('mdl_') and p.suffix!='.zip']
    dest=REPO/'design/square_counters_v2'
    for p in files:
        target=dest/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    archive=ROOT/'first_kernstown_18_painted_counters_review.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(f'Validated 18 unique RGBA sprites, zero portrait inserts; ZIP verified: {archive}')
if __name__=='__main__':main()
