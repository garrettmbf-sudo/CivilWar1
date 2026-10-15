"""Regression checks for the supplied schematic v3 map; NOT game validation."""
import unittest
from pathlib import Path
from valley_v3_connections import (EVEN, ODD, adjacent, port, traced_line,
                                   build_edges, audit_v3, source_routes,
                                   phantom_connections, RIVER_VARIANTS,
                                   RAIL_VARIANTS)
from validate_and_preview import parse_script, interp, W, H

SCRIPT = Path(__file__).with_name('build_valley_map_v3.ps1')

class ExactTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.net, cls.world = audit_v3(SCRIPT)
        cls.arrays, _ = parse_script(SCRIPT)

    def test_even_q_port_reciprocity(self):
        for x in (0,1,12,13,124):
            for y in (0,44,88):
                for d in range(6):
                    b=adjacent((x,y),d)
                    self.assertEqual(adjacent(b,(d+3)%6),(x,y))
                    self.assertEqual(port((x,y),b),d)

    def test_river_rail_sprite_masks_are_not_same_suffix(self):
        self.assertEqual(RIVER_VARIANTS[(0,4)],'River6')
        self.assertEqual(RAIL_VARIANTS[(0,4)],'Railroad9')
        self.assertEqual(RIVER_VARIANTS[(0,2)],'River7')
        self.assertEqual(RAIL_VARIANTS[(0,2)],'Railroad6')

    def test_all_traced_segments_are_adjacent(self):
        routes=source_routes(self.arrays)
        for kind, groups in routes.items():
            for name, waypoints in groups.items():
                track=traced_line(waypoints)
                self.assertEqual(track[0],waypoints[0], name)
                self.assertEqual(track[-1],waypoints[-1],name)
                for left,right in zip(track,track[1:]):
                    self.assertIn(port(left,right),range(6),name)

    def test_parallel_paths_do_not_get_phantom_links(self):
        net=build_edges({'river':{'a':[(2,4),(2,5)],'b':[(3,4),(3,5)]},
                         'road':{},'rail':{}},20,20)
        self.assertEqual(net['ports']['river'][(2,4)],{3})
        self.assertEqual(net['ports']['river'][(3,4)],{3})
        self.assertEqual(phantom_connections(net)['river'],3) # includes diagonal adjacency

    def test_ports_pair_at_exact_shared_hex_edges(self):
        for kind, shapes in self.net['ports'].items():
            for cell, dirs in shapes.items():
                for d in dirs:
                    self.assertIn((d+3)%6, shapes[adjacent(cell,d)], (kind,cell,d))
        self.assertFalse(self.report['defects'])

    def test_overlapping_towns_and_water_are_audited(self):
        names={v['town'] for v in self.report['town_on_river']}
        self.assertTrue({'Waynesboro','Port Republic','Front Royal'}.issubset(names))
        self.assertEqual(len(self.report['town_on_river']),4)

    def test_unverified_crossings_remain_unapproved(self):
        report=self.report
        unresolved={tuple(e['hex']) for e in report['unresolved_crossings']}
        approved=set(self.world['approved'])
        self.assertFalse(unresolved & approved)
        for e in report['rail_water_crossings_without_rail_bridge']:
            self.assertEqual(e['kind'],'rail')
        self.assertGreater(len(report['unresolved_crossings']),0)

    def test_v3_dimensions_and_river_forks_not_reversed(self):
        self.assertEqual((W,H),(125,130))
        xmass=interp(self.arrays['massanutten'],60)
        south=[x for x,y in self.net['occupancy']['river'] if y==60
               and 'riverSouthFork' in self.net['occupancy']['river'][(x,y)]]
        north=[x for x,y in self.net['occupancy']['river'] if y==60
               and 'riverNorthFork' in self.net['occupancy']['river'][(x,y)]]
        self.assertTrue(south and north)
        self.assertTrue(min(south)>xmass)
        self.assertTrue(max(north)<xmass)

if __name__=='__main__':
    unittest.main()
