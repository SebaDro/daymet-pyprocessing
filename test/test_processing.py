import unittest
from daymetpyprocessing import processing


class TestProcessing(unittest.TestCase):

    def setUp(self):
        self.__download_config_path = "data/test-processing-config.yml"

    def test_read_daymet_download_config(self):
        config = processing.read_daymet_preprocessing_config(self.__download_config_path)

        self.assertListEqual(config.ids, ["0", "1"])
        self.assertEqual(config.data_dir, "./data")
        self.assertEqual(config.output_dir,  "./output")
        self.assertEqual(config.output_format, "netcdf")
        self.assertListEqual(config.params["variables"], ["prcp", "tmax", "tmin"])
        self.assertEqual(config.version, "v4")
