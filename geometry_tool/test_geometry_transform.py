import unittest
import numpy as np
from geometry_transform import transform_record,map_boxes
class GeometryTests(unittest.TestCase):
    def test_landscape_integer_padding(self):
        r=transform_record([363,853]);self.assertEqual(r['resized_hw'],[285,672]);self.assertEqual(r['padding_ltrb'],[0,193,0,194])
    def test_portrait_integer_padding(self):
        r=transform_record([853,363]);self.assertEqual(r['resized_hw'],[672,285]);self.assertEqual(r['padding_ltrb'],[193,0,194,0])
    def test_known_edge_mapping(self):
        r=transform_record([100,200],[200,200]);a=np.asarray([[0,0,200,100]])
        np.testing.assert_array_equal(map_boxes(a,r),[[0,50,200,150]])
        np.testing.assert_array_equal(map_boxes([[0,50,200,150]],r,True),a)
    def test_odd_roundtrip(self):
        r=transform_record([363,853]);a=np.asarray([[1,3,850,360],[112.3,77.2,333.9,229.8]])
        np.testing.assert_allclose(map_boxes(map_boxes(a,r),r,True),a,rtol=0,atol=1e-10)
    def test_square_no_padding(self):self.assertEqual(transform_record([513,513])['padding_ltrb'],[0,0,0,0])
    def test_bad_dimensions(self):
        with self.assertRaises(ValueError):transform_record([0,100])
    def test_empty_boxes(self):self.assertEqual(map_boxes([],transform_record([100,200]),True).shape,(0,4))
if __name__=='__main__':unittest.main()
