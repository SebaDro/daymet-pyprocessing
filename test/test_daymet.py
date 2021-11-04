import unittest
from scripts import daymet
import datetime


class TestDaymet(unittest.TestCase):

    def setUp(self):
        self.__download_config_path = "data/test-download-config.yml"

    def test_read_daymet_download_config(self):
        config = daymet.read_daymet_download_config(self.__download_config_path)

        self.assertEqual(config.geo_file, "./data/features.geojson")
        self.assertEqual(config.id_col, "id")
        self.assertListEqual(config.ids, ["0", "1"])
        self.assertEqual(config.start_time, datetime.datetime.strptime("2000-01-01T12:00:00Z", "%Y-%m-%dT%H:%M:%S%z"))
        self.assertEqual(config.end_time, datetime.datetime.strptime("2010-12-31T12:00:00Z", "%Y-%m-%dT%H:%M:%S%z"))
        self.assertEqual(config.output_dir,  "./output")
        self.assertEqual(config.variable, "prcp")
        self.assertEqual(config.single_file_storage, True)
        self.assertEqual(config.version, "v4")

    def test_create_daymet_download_params(self):
        config = daymet.read_daymet_download_config(self.__download_config_path)
        params = daymet.create_daymet_download_params(config)

        self.assertEquals(len(params), 22)
        self.assertEquals(params[0].get_file_name(config.version), "daymet_v4_daily_na_prcp_2000.nc")
        self.assertEquals(params[0].get_request_url(config.version), "https://thredds.daac.ornl.gov/thredds/ncss/"
                                                                     "ornldaac/1840/daymet_v4_daily_na_prcp_2000.nc")
        self.assertEquals(params[0].year, 2000)
        self.assertEquals(params[0].variable, "prcp")
        self.assertEquals(params[0].feature_id, "0")
        self.assertEquals(params[0].north, 45.54704181508809)
        self.assertEquals(params[0].west, -95.68929057014608)
        self.assertEquals(params[0].east, -92.85889679495837)
        self.assertEquals(params[0].south, 42.23827162719258)
        self.assertEquals(params[0].start_time.strftime("%Y-%m-%dT%H:%M:%S%z"), "2000-01-01T12:00:00+0000")
        self.assertEquals(params[0].end_time.strftime("%Y-%m-%dT%H:%M:%S%z"), "2000-12-31T12:00:00+0000")
