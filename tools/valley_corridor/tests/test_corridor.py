"""Run from project folder: python -m unittest discover -s tests -v"""
import unittest, sys, json, math
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'src'))
import valley_corridor as vc

class GridTests(unittest.TestCase):
 def test_real_center_spacing_250yd(self):
  self.assertAlmostEqual(vc.DY,250*.9144,places=7)
 def test_across_flats_250yd(self):
  self.assertAlmostEqual(math.sqrt(3)*vc.R,250*.9144,places=7)
 def test_hex_projection_roundtrip(self):
  for col in range(7,vc.COLS,37):
   for row in range(12,vc.ROWS,31):
    self.assertEqual(vc.xy_hex(*vc.hex_xy(col,row)),(col,row))
 def test_neighbors_reciprocal(self):
  h=(24,30)
  for n in [(24,31),(24,29),(25,30),(25,29),(23,30),(23,29)]:
   self.assertEqual(vc.hex_dist(h,n),1)
   self.assertEqual(vc.hex_dist(n,h),1)
 def test_route_stop_order(self):
  self.assertEqual([p[0] for p in vc.STOPS],['Winchester','Kernstown','Newtown','Middletown','Strasburg',"Tom's Brook",'Woodstock','Edinburg','Mount Jackson','New Market'])
 def test_pike_unbroken(self):
  c,g=vc.pike_graph(vc.sample_route())
  self.assertGreater(len(c),300)
  self.assertEqual(len(c),len(set(c)))
  self.assertEqual(len(g[c[0]]),1);self.assertEqual(len(g[c[-1]]),1)
  self.assertTrue(all(len(g[n])==2 for n in c[1:-1]))
  self.assertTrue(all(vc.hex_dist(a,b)==1 for a,b in zip(c,c[1:])))
 def test_entry_exits_opposite(self):
  opposite={'E':'W','NE':'SW','NW':'SE','W':'E','SW':'NE','SE':'NW'}
  c,g=vc.pike_graph(vc.sample_route())
  for a,b in zip(c,c[1:]):self.assertEqual(vc.heading_between(b,a),opposite[vc.heading_between(a,b)])
 def test_boundaries(self):
  c,g=vc.pike_graph(vc.sample_route())
  self.assertTrue(all(0<=col<vc.COLS and 0<=row<vc.ROWS for col,row in c))
 def test_landmarks_in_map(self):
  for name,lon,lat in vc.STOPS:
   a,b=vc.lonlat_hex(lon,lat)
   self.assertTrue(0<=a<vc.COLS and 0<=b<vc.ROWS,name)
 def test_no_connecting_rail(self):
  data=json.loads((P/'data'/'corridor_topology.json').read_text())
  self.assertTrue(data['rules']['no_winchester_strasburg_railroad'])
  self.assertEqual(len([a for a in data['networks'] if 'rail' in a]),1)
 def test_source_confidence_explicit(self):
  d=json.loads((P/'data'/'corridor_topology.json').read_text())
  self.assertIn('PROTOTYPE',d['status'])
  self.assertIn('MISSING',d['rules']['terrain_dem'])
  self.assertEqual(d['rules']['crossings'],'not traversable until separately verified')
 def test_exported_native_images(self):
  from PIL import Image
  files=list((P/'tiles_demo').glob('SV_CORRIDOR_*.png'))
  self.assertEqual(len(files),9)
  for f in files:
   im=Image.open(f)
   self.assertEqual(im.size,(2000,2000))
   self.assertEqual(im.convert('RGBA').getpixel((0,0))[3],0)
 def test_image_provenance(self):
  j=json.loads((P/'qa'/'native_slice_checks.json').read_text())
  self.assertEqual(j['stitch_original_pixel_mismatches'],0)
  self.assertGreater(j['stitch_original_pixel_samples'],500)
 def test_compression_stays_pixel_exact(self):
  j=json.loads((P/'qa'/'compression_summary.json').read_text())
  self.assertTrue(j['png_identical'])
 def test_full_grid_is_large(self):
  self.assertGreater(vc.COLS*vc.ROWS,50000)

if __name__=='__main__':unittest.main()