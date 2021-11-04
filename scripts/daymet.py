import datetime
import geopandas as gpd
import yaml
import requests as req
import h5netcdf
import xarray as xr
from io import BytesIO

daymet_proj_str = "+proj = lcc + lat_1 = 25 + lat_2 = 60 + lat_0 = 42.5 + lon_0 = -100 + x_0 = 0 + y_0 = 0 + ellps = " \
                  "WGS84 + units = m + no_defs "


class DaymetDownloadConfig:
    def __init__(self, geo_file: str, id_col: str, ids: list, variable: str, start_time: datetime.datetime,
                 end_time: datetime.datetime, output_dir: str, single_file_storage: bool, version: str):
        self.__geo_file = geo_file
        self.__id_col = id_col
        self.__ids = ids
        self.__variable = variable
        self.__start_time = start_time
        self.__end_time = end_time
        self.__output_dir = output_dir
        self.__single_file_storage = single_file_storage
        self.__version = version

    @property
    def geo_file(self):
        return self.__geo_file

    @property
    def id_col(self):
        return self.__id_col

    @property
    def ids(self):
        return self.__ids

    @property
    def variable(self):
        return self.__variable

    @property
    def start_time(self):
        return self.__start_time

    @property
    def end_time(self):
        return self.__end_time

    @property
    def output_dir(self):
        return self.__output_dir

    @property
    def single_file_storage(self):
        return self.__single_file_storage

    @property
    def version(self):
        return self.__version


class DaymetDownloadParameters:
    def __init__(self, year: int, variable: str, feature_id: str, north: float, west: float, east: float, south: float,
                 start_time: datetime.datetime, end_time: datetime.datetime):
        self.__base_url_v3 = "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1328/"
        self.__base_url_v4 = "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1840/"
        self.__year = year
        self.__variable = variable
        self.__feature_id = feature_id
        self.__north = north
        self.__west = west
        self.__east = east
        self.__south = south
        self.__start_time = start_time
        self.__end_time = end_time

    @property
    def year(self):
        return self.__year

    @property
    def variable(self):
        return self.__variable

    @property
    def feature_id(self):
        return self.__feature_id

    @property
    def north(self):
        return self.__north

    @property
    def west(self):
        return self.__west

    @property
    def east(self):
        return self.__east

    @property
    def south(self):
        return self.__south

    @property
    def start_time(self):
        return self.__start_time

    @property
    def end_time(self):
        return self.__end_time

    def get_file_name(self, version: str):
        if version == "v3":
            return self._get_v3_file_name()
        elif version == "v4":
            return self._get_v4_file_name()
        else:
            print("Unsupported version {}. Returned v4 file name.".format(version))
            return self._get_v4_file_name()

    def get_request_url(self, version: str):
        if version == "v3":
            return self._get_v3_request_url()
        elif version == "v4":
            return self._get_v4_request_url()
        else:
            print("Unsupported version {}. Returned v4 URL.".format(version))
            return self._get_v4_request_url()

    def _get_v3_file_name(self):
        return "daymet_v3_{}_{}_na.nc4".format(self.__variable, str(self.__year))

    def _get_v4_file_name(self):
        return "daymet_v4_daily_na_{}_{}.nc".format(self.__variable, str(self.__year))

    def _get_v3_request_url(self):
        return self.__base_url_v3\
               + str(self.__year) + "/"\
               + self._get_v3_file_name()

    def _get_v4_request_url(self):
        return self.__base_url_v4\
               + self._get_v4_file_name()

    def get_params_dict(self) -> dict:
        """
        Create a dict that holds the request parameters for requesting a certain dataset from the NetCDF Subset Service
        for Daymet data

        Returns
        -------
        dict
            Contains the request parameters

        """
        return {"var": self.__variable,
               "north": str(self.__north),
               "west": str(self.__west),
               "east": str(self.__east),
               "south": str(self.__south),
               "horizStride": "1",
               "time_start": self.__start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "time_end": self.__end_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
               "timeStride": "1",
               "accept": "netcdf4"}


class DaymetPreprocessingConfig:
    def __init__(self, automatic_mode: bool, features: list, directory: str, variables: list, version: str):
        self.__automatic_mode = automatic_mode
        self.__features = features
        self.__directory = directory
        self.__variables = variables
        self.__version = version

    @property
    def automatic_mode(self):
        return self.__automatic_mode

    @property
    def features(self):
        return self.__features

    @property
    def directory(self):
        return self.__directory

    @property
    def variables(self):
        return self.__variables

    @property
    def version(self):
        return self.__version


def read_daymet_download_config(path: str) -> DaymetDownloadConfig:
    """
    Reads configuration parameters from a *.yml file.

    Parameters
    ----------
    path: str
        Path to the configuration file

    Returns
    -------
    DaymetDownloadConfig
        Object containing config parameters controlling the download process for Daymet data

    """
    with open(path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            start_time = datetime.datetime.strptime(config["timeFrame"]["startTime"], "%Y-%m-%dT%H:%M:%S%z")
            end_time = datetime.datetime.strptime(config["timeFrame"]["endTime"], "%Y-%m-%dT%H:%M:%S%z")
            return DaymetDownloadConfig(config["geo"]["file"], config["geo"]["idCol"], config["geo"]["ids"],
                                        config["variable"], start_time, end_time, config["outputDir"],
                                        config["singleFileStorage"], config["version"])
        except yaml.YAMLError as ex:
            print("Error reading daymet file {}".format(ex))
        except KeyError as ex:
            print("Missing config parameter: {}".format(ex))
        except ValueError as ex:
            print("No valid format for 'timeFrame' value\n{}".format(ex))


def create_daymet_download_params(config: DaymetDownloadConfig) -> list:
    """
    Creates a list of DaymetDownloadParameters from config parameters

    Parameters
    ----------
    config: DaymetDownloadConfig
        Config parameters for controlling the download process

    Returns
    -------
    list
        List containing DaymetDownloadParameters. Each entry can be used for requestinga single dataset from the NetCDF
        Subset Service for Daymet data

    """
    params_list = []

    features = gpd.read_file(config.geo_file)
    for feature_id in config.ids:
        features[config.id_col] = features[config.id_col].astype(str)
        feature = features[features[config.id_col] == feature_id]
        minx = feature.total_bounds[0]
        miny = feature.total_bounds[1]
        maxx = feature.total_bounds[2]
        maxy = feature.total_bounds[3]

        if (config.end_time.year - config.start_time.year) == 0:
            params_list.append(DaymetDownloadParameters(year=config.start_time.year, variable=config.variable,
                                                        feature_id=feature_id, west=minx, south=miny, east=maxx,
                                                        north=maxy, start_time=config.start_time,
                                                        end_time=config.end_time))
            return params_list
        elif (config.end_time.year - config.start_time.year) >= 1:
            start_year_start_time = config.start_time
            start_year_end_time = datetime.datetime.strptime("{}-12-31T12:00:00Z".format(config.start_time.year), "%Y-%m-%dT%H:%M:%S%z")
            start_year_params = DaymetDownloadParameters(year=config.start_time.year, variable=config.variable,
                                                         feature_id=feature_id, west=minx, south=miny, east=maxx,
                                                         north=maxy, start_time=start_year_start_time,
                                                         end_time=start_year_end_time)

            params_list.append(start_year_params)

            for year in range(config.start_time.year + 1, config.end_time.year):
                start_time = datetime.datetime.strptime("{}-01-01T12:00:00Z".format(year), "%Y-%m-%dT%H:%M:%S%z")
                end_time = datetime.datetime.strptime("{}-12-31T12:00:00Z".format(year), "%Y-%m-%dT%H:%M:%S%z")
                params_list.append(DaymetDownloadParameters(year=year, variable=config.variable,
                                                            feature_id=feature_id, west=minx, south=miny, east=maxx,
                                                            north=maxy, start_time=start_time, end_time=end_time))

            end_year_start_time = datetime.datetime.strptime("{}-01-01T12:00:00Z".format(config.end_time.year), "%Y-%m-%dT%H:%M:%S%z")
            end_year_end_time = config.end_time
            end_year_params = DaymetDownloadParameters(year=config.end_time.year, variable=config.variable,
                                                       feature_id=feature_id, west=minx, south=miny, east=maxx,
                                                       north=maxy, start_time=end_year_start_time,
                                                       end_time=end_year_end_time)
            params_list.append(end_year_params)
        else:
            raise ValueError("Can't create download params for negative timespan {} to {}"
                             .format(config.start_time, config.end_time))
    return params_list


def download_daymet(params: DaymetDownloadParameters, outpath: str, version: str):
    """
    Downloads a certain dataset in NetCDF format from the NetCDF Subset Service for Daymet data by using the given
    DaymetDownloadParameters.

    Parameters
    ----------
    params: DaymetDownloadParameters
        Parameters used for a single request
    outpath: str
        Path to store the downloaded NetCDF file
    version: str
        Version of the Daymet dataset (supported: v3, v4)

    """
    r = req.get(params.get_request_url(version), params=params.get_params_dict())
    if r.status_code != req.codes.ok:
        r.raise_for_status()
    f = open("{}/{}/{}_{}".format(outpath, params.feature_id, params.feature_id, params.get_file_name(version)), "wb")
    f.write(r.content)
    f.close()


def download_and_merge_multiple_daymet_datasets(feature: str, params_list: list, outpath: str, version: str):
    """
    Downloads multiple datasets in NetCDF format from the NetCDF Subset Service for Daymet data for a single feature using
    the given list of DaymetDownloadParameters. The single NetCDF datasets will be concatenated and stored within a
    single file.

    Parameters
    ----------
    feature: str
        The feature to download different datasets for
    params_list: list
        List of request parameters
    outpath: str
        Path to store the datasets within a single NetCDF file
    version: str
        Version of the Daymet dataset (supported: v3, v4)

    """
    ds_list = []
    counter = 0
    for params in params_list:
        counter += 1
        print("Downloading Daymet file {} from {}: {} for feature {}"
              .format(counter, len(params_list), params.get_file_name(version), params.feature_id), end="\r")
        r = req.get(params.get_request_url(version), params=params.get_params_dict())
        if r.status_code != req.codes.ok:
            r.raise_for_status()
        with xr.open_dataset(BytesIO(r.content), engine="h5netcdf") as ds:
            ds_list.append(ds)
    result = xr.concat(ds_list, dim="time").sortby("time")
    if version == "v3":
        result.to_netcdf("{}/{}_daymet_v3_{}_na.nc4".format(outpath, feature, params.variable))
    elif version == "v4":
        result.to_netcdf("{}/{}_daymet_v4_daily_na_{}.nc4".format(outpath, feature, params.variable))
    else:
        result.to_netcdf("{}/{}_daymet_v4_daily_na_{}.nc4".format(outpath, feature, params.variable))
    print("\nFinished downloading {} Daymet files\n".format(counter))
