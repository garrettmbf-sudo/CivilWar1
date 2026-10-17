"""Asset identity and map-layout validation, without proprietary game libraries."""
import base64,hashlib,json,math,unittest,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageChops
D=Path(__file__).resolve().parent
EXPECTED={'mdl_CSA_RGarnett.png':'78f729055b7593e993448dab07e2e62f2f7a8695','mdl_CSA_TAshby.png':'012659f729c5a9a8b803eb875d56906826007ba2','mdl_CSA_TJJackson.png':'fb3e728765bbb2bf7c50f281fc91d87eee60530b','mdl_USA_EBTyler.png':'2117a4838e2a6aa74a4b9bf5a70dd79008360fdf','mdl_USA_JCSullivan.png':'b79ea1f42b559d0f0de42998aaf6abc0bbc20e2f','mdl_USA_NKimball.png':'0aa272d9217464d1dce0c18d19f60450ad27f53c'}
class CounterAssets(unittest.TestCase):
 def test_approved_source_bytes(self):
  for name,expected in EXPECTED.items():
   b=(D/'source'/name).read_bytes();self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),expected)
 def test_embedded_portraits_and_no_crops(self):
  roster=json.loads((D/'roster.json').read_text())
  for style in 'abcde':
   for u in roster:
    root=ET.parse(D/'masters'/f'{style}_{u["id"]}.svg').getroot();self.assertFalse(list(root.iter('{http://www.w3.org/2000/svg}clipPath')))
    if u['portrait']:
     images=list(root.iter('{http://www.w3.org/2000/svg}image'));data=[base64.b64decode(i.attrib['href'].split(',')[1]) for i in images];self.assertIn((D/'source'/u['portrait']).read_bytes(),data)
 def test_preferred_brigades_use_soldiers_and_hq_uses_face(self):
  ns='{http://www.w3.org/2000/svg}'
  brigade=ET.parse(D/'masters/e_k01.svg').getroot();hq=ET.parse(D/'masters/e_k19.svg').getroot()
  self.assertEqual(len(list(brigade.iter(ns+'image'))),4)
  self.assertEqual(len(list(hq.iter(ns+'image'))),1)
  # Commander name text must fit vertically inside its banner, above the stats.
  for file in (D/'masters').glob('*.svg'):
   root=ET.parse(file).getroot();rects=list(root.iter(ns+'rect'));footer=next(r for r in rects if r.attrib.get('height')=='33');fy=float(footer.attrib['y'])
   labels=[t for t in root.iter(ns+'text') if t.attrib.get('font-family')=='Georgia']
   self.assertEqual(len(labels),1);baseline=float(labels[0].attrib['y']);self.assertGreaterEqual(baseline-18,fy);self.assertLessEqual(baseline+5,fy+33)
 def test_deployment_preserved(self):
  raw=json.loads((D.parents[1]/'data/layers/kernstown_units.json').read_text())['units'];r=json.loads((D/'roster.json').read_text());self.assertEqual(len(r),20)
  self.assertEqual([(u['col'],u['row']) for u in raw],[(u['col'],u['row']) for u in r[:18]])
  self.assertTrue(all('stress-test' in u['placement'] for u in r[18:]))
  self.assertIsNone(next(u for u in r if u['name']=='BURKS')['portrait']);self.assertIsNone(next(u for u in r if u['name']=='FULKERSON')['portrait'])
 def test_transparent_raster_exports(self):
  for size in [512,256,128]:
   paths=list((D/'sprites'/str(size)).glob('*.png'));self.assertEqual(len(paths),105)
   for p in paths:
    with Image.open(p) as im:
     self.assertEqual(im.mode,'RGBA');self.assertEqual(im.size,(size,size));a=im.getchannel('A');self.assertEqual(a.getpixel((0,0)),0);self.assertEqual(a.getextrema(),(0,255))
 def test_dense_counter_clearance(self):
  coords=[(16+i%5,23+i//5) for i in range(20)]
  for style in 'abcde':
   masks=[]
   for i,(c,r) in enumerate(coords):
    im=Image.open(D/'sprites/512'/f'{style}_k{i+1:02}.png').resize((70,70),Image.Resampling.LANCZOS).getchannel('A').point(lambda a:255 if a>127 else 0)
    m=Image.new('L',(600,600));x=round(66*(c-16)+30);y=round(math.sqrt(3)*44*(r-23+.5*(c&1))+30);m.paste(im,(x,y))
    for prior in masks:self.assertIsNone(ImageChops.multiply(m,prior).getbbox(),f'{style}: alpha collision')
    masks.append(m)
 def test_atlas_frames_match_individual_sprites(self):
  manifest=json.loads((D/'sprites/atlas_manifest.json').read_text());self.assertEqual(manifest['pivot_normalized'],[.5,.5])
  for s,entry in manifest['atlases'].items():
   atlas=Image.open(D/'sprites'/entry['file']);self.assertEqual(len(entry['frames']),20)
   for id,frame in entry['frames'].items():
    x,y,w,h=frame['rect'];single=Image.open(D/'sprites/512'/f'{s.lower()}_{id}.png');self.assertEqual(atlas.crop((x,y,x+w,y+h)).tobytes(),single.tobytes())
if __name__=='__main__':unittest.main()
