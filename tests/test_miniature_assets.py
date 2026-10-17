"""Check preservation, manifest gates, native sizing, and delivered PNGs."""
import json
from pathlib import Path
import pytest
from PIL import Image
from scripts.build_miniature_assets import ART, ROOT, digest, portrait_source
from scripts.preview_miniature_assets import screen_size

def test_portrait_sources_still_match_receipt():
    receipt=json.loads((ART/'evidence/build_receipt.json').read_text())
    for row in receipt:
        assert digest(ROOT/row['source']) == row['source_sha256']

def test_missing_portrait_is_blank_and_unknown_is_rejected():
    assert portrait_source('mdl_CSA_JSBurks.png') is None
    assert portrait_source('mdl_CSA_SVFulkerson.png') is None
    with pytest.raises(KeyError):portrait_source('invented.png')

def test_review_exports_and_margins():
    for unit in json.loads((ART/'asset_manifest.json').read_text())['units']:
        for size in (512,1024):
            path=ART/'sprites'/str(size)/unit['country']/(unit['name']+'.png')
            im=Image.open(path)
            assert im.mode=='RGBA' and im.size==(size,size)
            box=im.getchannel('A').getbbox()
            assert min(box[0],box[1],size-box[2],size-box[3]) >= size*.065
            assert im.getchannel('A').getextrema()==(0,255)

def test_measured_scale_and_resolution_trap():
    assert screen_size(1024,20)==pytest.approx(102.2976)
    assert screen_size(1024,40)==pytest.approx(screen_size(1024,20)/2)
    # A 512 SOURCE image is half the world size, despite identical loaded width.
    assert screen_size(512,20)==pytest.approx(screen_size(1024,20)/2)

def test_assets_exist_in_specified_opening_snapshot():
    snapshot=json.loads((ART/'evidence/opening_snapshot.json').read_text())
    ids={r['formation_id'] for r in snapshot['counters']}|set(snapshot['headquarters'])
    assert snapshot['date']=='1862-03-23'
    for u in json.loads((ART/'asset_manifest.json').read_text())['units']:assert u['id'] in ids
