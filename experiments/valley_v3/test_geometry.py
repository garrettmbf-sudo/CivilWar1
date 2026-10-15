"""Geometry-only regression tests. Does not verify engine compatibility."""
import unittest
from validate_and_preview import W, H, parse_script, build, audit, trace, ROOT

class MapGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arrays, cls.tables = parse_script(ROOT / 'build_valley_map_v3.ps1')
        cls.map = build(cls.arrays, cls.tables)

    def test_dimensions_and_terrain(self):
        self.assertEqual((W,H),(125,130))
        self.assertEqual(len(self.map['terrain']),W*H)
        self.assertEqual(len(self.map['towns']),33)

    def test_towns_and_segments(self):
        self.assertEqual(audit(self.map),[])

    def test_no_unauthorized_ridge_shortcuts(self):
        self.assertFalse(self.map['blocked'])

    def test_valley_pike_tiles_stay_traversable(self):
        pike=trace(self.arrays['valleyPike'])
        self.assertTrue(pike)
        for x,y in pike:
            # 11 is the single FilterRoadBridge hex, the only non-engineer crossing.
            self.assertIn(self.map['terrain'][y*W+x], (6,7,8,11), (x,y))

    def test_one_bridge_tile_per_named_site(self):
        by_name = {}
        for p, site in self.map['approved'].items():
            by_name.setdefault(site['Name'], []).append(p)
        for name, pts in by_name.items():
            self.assertEqual(len(pts), 1, name)
            x, y = pts[0]
            if (x, y) not in self.map['towns']:
                self.assertEqual(self.map['terrain'][y*W+x], 11, name)

    def test_bridge_collisions_are_classified(self):
        joint=self.map['river']&(self.map['road']|self.map['rail'])
        self.assertEqual(joint,set(self.map['approved'])|self.map['unresolved'])
        self.assertFalse(set(self.map['approved'])&self.map['unresolved'])

    def test_unresolved_are_rendered_as_obstacles(self):
        for x,y in self.map['unresolved']:
            if (x,y) in self.map['towns']:
                continue  # Towns take precedence; crossing still reported for review.
            self.assertEqual(self.map['terrain'][y*W+x],5)

if __name__=='__main__':
    unittest.main()
