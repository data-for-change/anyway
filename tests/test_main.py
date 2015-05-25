import unittest
from main import parse_data
from models import Marker

class TestParseData(unittest.TestCase):

  def setUp(self):
      self.marker_dummy = dict(type=1, title="test title", description="test description", latitude=1, longitude=1)
      self.bad_marker_dummy = dict(type=1, title="No properties")

  def tearDown(self):
    self.marker_dummy = None
    self.bad_marker_dummy = None

  class NoParsedObject(object):
    """docstring for ClassName"""
    def __init__(self, arg):
      self.arg = arg

  def test_class_null(self): 
    self.assertEqual(parse_data(None, self.marker_dummy), None)

  def test_data_null(self):
    self.assertEqual(parse_data(Marker, None), None)

  def test_bad_data_format_marker_class(self):
    self.assertEqual(parse_data(Marker, self.bad_marker_dummy), None)

  def test_class_without_parse_method(self):
    self.assertEqual(parse_data(self.NoParsedObject, self.marker_dummy), None)

  def test_parse_marker(self):
    marker  = parse_data(Marker, self.marker_dummy)
    for key in self.marker_dummy:
      self.assertEqual(marker.__dict__[key], self.marker_dummy[key])

if __name__ == '__main__':
    unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestParseData)
    unittest.TextTestRunner(verbosity=2).run(suite)
