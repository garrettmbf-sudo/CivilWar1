"""Topology regression tests: run `python -m unittest -v test_port_validation.py`."""
import copy
import unittest
import sys
from pathlib import Path
# In the repository tests/ is a sibling of tools/edge_qa; local standalone
# QA archives keep tests and modules together in one directory.
repo_tools = Path(__file__).resolve().parents[1] / "tools" / "edge_qa"
if repo_tools.is_dir():
    sys.path.insert(0, str(repo_tools))
from port_validation import validate_network


def example():
    a={"orientation":"flat_top","ports":{"1":[{"kind":"pike","position":.5,"width":.11,"material":"macadam"}]},"heights":{"1":[101,102,103]}}
    b={"orientation":"flat_top","ports":{"4":[{"kind":"pike","position":.5,"width":.11,"material":"macadam"}]},"heights":{"4":[103,102,101]}}
    return {"tiles":{"A":a,"B":b},"adjacencies":[{"a":{"tile":"A","edge":1},"b":{"tile":"B","edge":4}}]}


class EdgeValidationTests(unittest.TestCase):
    def test_valid_pike_passes(self):self.assertEqual([],validate_network(example()))
    def test_missing_pike_fails(self):
        x=example();x['tiles']['B']['ports']['4']=[]
        self.assertIn('DANGLING', ' '.join(validate_network(x)))
    def test_feature_kind_mismatch_fails(self):
        x=example();x['tiles']['B']['ports']['4'][0]['kind']='rail'
        self.assertIn('DISCONNECTED', ' '.join(validate_network(x)))
    def test_road_width_mismatch_fails(self):
        x=example();x['tiles']['B']['ports']['4'][0]['width']=.23
        self.assertIn('WIDTH SEAM',' '.join(validate_network(x)))
    def test_wrong_opposite_edge_fails(self):
        x=example();x['adjacencies'][0]['b']['edge']=3
        self.assertIn('Wrong opposite edge',' '.join(validate_network(x)))
    def test_material_mismatch_fails(self):
        x=example();x['tiles']['B']['ports']['4'][0]['material']='mud'
        self.assertIn('MATERIAL SEAM',' '.join(validate_network(x)))
    def test_elevation_crack_fails(self):
        x=example();x['tiles']['B']['heights']['4'][1]=120
        self.assertIn('ELEVATION CRACK',' '.join(validate_network(x)))
    def test_point_top_art_blocked(self):
        x=example();x['tiles']['B']['orientation']='point_top'
        self.assertIn('shape must be flat_top',' '.join(validate_network(x)))
    def test_unpaired_port_fails(self):
        x=example();x['tiles']['B']['ports']['3']=[{"kind":"river","position":.5,"width":.25,"material":"silt"}]
        self.assertIn('UNPAIRED INTERIOR EXIT',' '.join(validate_network(x)))
    def test_verified_outside_exit_allowed(self):
        x=example();x['tiles']['B']['ports']['3']=[{"kind":"river","position":.5,"width":.25,"material":"silt"}]
        x['perimeter_exits']=[{"tile":"B","edge":3}]
        self.assertEqual([],validate_network(x))
    def test_crossing_needs_historical_source(self):
        x=example();x['tiles']['A']['crossings']=[{"type":"covered_bridge"}]
        self.assertIn('historical source',' '.join(validate_network(x)))
    def test_crossing_requires_supported_type(self):
        x=example();x['tiles']['A']['crossings']=[{"type":"automatic_bridge","source":"invented"}]
        self.assertIn('not verified type',' '.join(validate_network(x)))
    def test_multiport_offset_mismatch_fails(self):
        x=example();x['tiles']['B']['ports']['4'][0]['position']=.25
        self.assertIn('DISCONNECTED',' '.join(validate_network(x)))
    def test_shared_heights_reversal(self):
        x=example();x['tiles']['B']['heights']['4']=[101,102,103]
        self.assertIn('ELEVATION CRACK',' '.join(validate_network(x)))

if __name__=='__main__': unittest.main()