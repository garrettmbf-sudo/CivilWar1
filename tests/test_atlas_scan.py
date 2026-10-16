"""Synthetic shape and edge-profile smoke tests for the illustrative audit."""
import unittest
import numpy as np
import cv2
from validate_tile_edges import assess_shape, compare_profiles, foreground, hex_vertices

class ImageGeometryTests(unittest.TestCase):
    def make(self,orientation):
        im=np.full((400,420,3),170,dtype=np.uint8)
        pts=hex_vertices((30,20,360,360),orientation).astype(np.int32)
        cv2.fillPoly(im,[pts],(30,125,183))  # BGR ochre
        return im
    def test_point_top_shape(self):
        im=self.make('point_top');found=assess_shape(im,foreground(im),(0,0,420,400))
        self.assertIsNotNone(found)
        self.assertEqual(found[4], 'point_top')
    def test_flat_top_shape(self):
        im=self.make('flat_top');found=assess_shape(im,foreground(im),(0,0,420,400))
        self.assertIsNotNone(found)
        self.assertEqual(found[4], 'flat_top')
    def test_near_identical_edges(self):
        a=np.full((64,3),130,dtype=np.float32)
        b=np.full((64,3),130,dtype=np.float32)
        self.assertEqual((0.,0.),compare_profiles(a,b))
    def test_different_edges(self):
        a=np.full((64,3),120,dtype=np.float32)
        b=np.full((64,3),220,dtype=np.float32)
        self.assertGreater(compare_profiles(a,b)[0],100)

if __name__=='__main__': unittest.main()