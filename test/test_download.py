import unittest
from scripts import download
import datetime


class TestDownload(unittest.TestCase):

    def setUp(self):
        self.__download_config_path = "data/test-download-config.yml"

    def test_read_daymet_download_config(self):
        config = download.read_daymet_download_config(self.__download_config_path)

        self.assertEqual("./data/features.geojson", config.geo_file)
        self.assertEqual("id", config.id_col)
        self.assertListEqual(["0", "1"], config.ids)
        self.assertEqual(datetime.datetime.strptime("2000-01-01T12:00:00", "%Y-%m-%dT%H:%M:%S"), config.start_time)
        self.assertEqual(datetime.datetime.strptime("2010-12-31T12:00:00", "%Y-%m-%dT%H:%M:%S"), config.end_time)
        self.assertEqual("./output", config.output_dir)
        self.assertEqual("prcp", config.variable)
        self.assertEqual(True, config.single_file_storage)
        self.assertEqual("v4", config.version)

    def test_create_daymet_download_params(self):
        config = download.read_daymet_download_config(self.__download_config_path)
        params = download.create_daymet_download_params_from_config(config)

        self.assertEqual(22, len(params))
        self.assertEqual("daymet_v4_daily_na_prcp_2000.nc", params[0].get_file_name(config.version))
        self.assertEqual("https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1840/daymet_v4_daily_na_prcp_2000.nc",
                         params[0].get_request_url(config.version))
        self.assertEqual(2000, params[0].year)
        self.assertEqual("prcp", params[0].variable)
        self.assertEqual("0", params[0].name)
        self.assertEqual(45.54704181508809, params[0].north)
        self.assertEqual(-95.68929057014608, params[0].west)
        self.assertEqual(-92.85889679495837, params[0].east)
        self.assertEqual(42.23827162719258, params[0].south)
        self.assertEqual("2000-01-01T12:00:00", params[0].start_time.strftime("%Y-%m-%dT%H:%M:%S"))
        self.assertEqual("2000-12-31T12:00:00", params[0].end_time.strftime("%Y-%m-%dT%H:%M:%S"))

        self.assertEqual("2000-01-01T12:00:00Z", params[0].get_params_dict()["time_start"])
        self.assertEqual("2000-12-31T12:00:00Z", params[0].get_params_dict()["time_end"])
