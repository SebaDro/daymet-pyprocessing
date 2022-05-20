import datetime
import geopandas as gpd
import yaml
import logging
import requests as req
import h5netcdf
import xarray as xr
import os
from io import BytesIO

logger = logging.getLogger(__name__)

daymet_proj_str = "+proj = lcc + lat_1 = 25 + lat_2 = 60 + lat_0 = 42.5 + lon_0 = -100 + x_0 = 0 + y_0 = 0 + ellps = " \
                  "WGS84 + units = m + no_defs "


class DaymetDownloadConfig:
    def __init__(self, name: str, variable: str, start_time: datetime.datetime, end_time: datetime.datetime,
                 output_dir: str, single_file_storage: bool, version: str, read_timeout: int):
        self.__name = name
        self.__variable = variable
        self.__start_time = start_time
        self.__end_time = end_time
        self.__output_dir = output_dir
        self.__single_file_storage = single_file_storage
        self.__version = version
        self.__read_timeout = read_timeout

    @property
    def name(self):
        return self.__name

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

    @property
    def read_timeout(self):
        return self.__read_timeout


class DaymetDownloadGeofileConfig(DaymetDownloadConfig):
    def __init__(self, geo_file: str, id_col: str, ids: list, name: str, variable: str, start_time: datetime.datetime,
                 end_time: datetime.datetime, output_dir: str, single_file_storage: bool, version: str, read_timeout: int):
        super().__init__(name, variable, start_time, end_time, output_dir, single_file_storage, version, read_timeout)
        self.__geo_file = geo_file
        self.__id_col = id_col
        self.__ids = ids

    @property
    def geo_file(self):
        return self.__geo_file

    @property
    def id_col(self):
        return self.__id_col

    @property
    def ids(self):
        return self.__ids

    @ids.setter
    def ids(self, value):
        self.__ids = value


class DaymetDownloadBboxConfig(DaymetDownloadConfig):
    def __init__(self, bbox: list, name: str, variable: str, start_time: datetime.datetime,
                 end_time: datetime.datetime, output_dir: str, single_file_storage: bool, version: str, read_timeout: int):
        super().__init__(name, variable, start_time, end_time, output_dir, single_file_storage, version, read_timeout)
        self.__bbox = bbox

    @property
    def bbox(self):
        return self.__bbox


class DaymetDownloadParameters:
    def __init__(self, year: int, variable: str, name: str, north: float, west: float, east: float, south: float,
                 start_time: datetime.datetime, end_time: datetime.datetime):
        self.__base_url_v3 = "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1328/"
        self.__base_url_v4 = "https://thredds.daac.ornl.gov/thredds/ncss/ornldaac/1840/"
        self.__year = year
        self.__variable = variable
        self.__name = name
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
    def name(self):
        return self.__name

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
            logger.warning(f"Unsupported version {version}. Returned v4 file name.")
            return self._get_v4_file_name()

    def get_request_url(self, version: str):
        if version == "v3":
            return self._get_v3_request_url()
        elif version == "v4":
            return self._get_v4_request_url()
        else:
            logger.warning(f"Unsupported version {version}. Returned v4 URL.")
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
               "time_start": self.__start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "time_end": self.__end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "timeStride": "1",
               "accept": "netcdf4"}


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
            start_time = datetime.datetime.strptime(config["timeFrame"]["startTime"], "%Y-%m-%dT%H:%M:%S")
            end_time = datetime.datetime.strptime(config["timeFrame"]["endTime"], "%Y-%m-%dT%H:%M:%S")
            if "bbox" in config:
                return DaymetDownloadBboxConfig(config["bbox"], config["name"], config["variable"], start_time, end_time,
                                                config["outputDir"], config["singleFileStorage"], config["version"], config["readTimeout"])
            elif "geo" in config:
                ids = None
                if "ids" in config["geo"]:
                    ids = config["geo"]["ids"]
                return DaymetDownloadGeofileConfig(config["geo"]["file"], config["geo"]["idCol"], ids, config["name"],
                                                   config["variable"], start_time, end_time, config["outputDir"],
                                                   config["singleFileStorage"], config["version"], config["readTimeout"])
            else:
                raise ValueError("Config must contain at least one of the following definitions: 'geo', 'bbox'}")
        except yaml.YAMLError:
            logger.exception(f"Error reading daymet file.")
        except KeyError as ex:
            logger.exception(f"Missing config parameter.")
        except ValueError as ex:
            logger.exception(f"No valid format for 'timeFrame' value.")


def create_daymet_download_params_from_config(config: DaymetDownloadConfig) -> list:
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

    if isinstance(config, DaymetDownloadBboxConfig):
        minx = config.bbox[0]
        miny = config.bbox[1]
        maxx = config.bbox[2]
        maxy = config.bbox[3]
        params_list = create_daymet_download_params(config.start_time, config.end_time, config.variable,
                                                    config.name, minx, miny, maxx, maxy)
    elif isinstance(config, DaymetDownloadGeofileConfig):
        params_list = []
        features = gpd.read_file(config.geo_file)
        features[config.id_col] = features[config.id_col].astype(str)
        if config.ids is None:
            config.ids = features[config.id_col].tolist()
        for feature_id in config.ids:
            feature = features[features[config.id_col] == feature_id]
            if feature.empty:
                logger.warning(f"No feature with id {feature_id} exists in file {config.geo_file}. Download will be skipped.")
            else:
                minx = feature.total_bounds[0]
                miny = feature.total_bounds[1]
                maxx = feature.total_bounds[2]
                maxy = feature.total_bounds[3]

                params = create_daymet_download_params(config.start_time, config.end_time, config.variable,
                                                            feature_id, minx, miny, maxx, maxy)
                params_list =params_list + params
    return params_list


def create_daymet_download_params(start_time, end_time, variable, name, minx, miny, maxx, maxy) -> list:
    """
    Creates a list of DaymetDownloadParameters from DaymetDownloadBboxConfig parameters

    Parameters
    ----------
    maxy
    maxx
    miny
    minx
    name
    variable
    end_time
    start_time

    Returns
    -------
    list
        List containing DaymetDownloadParameters. Each entry can be used for requesting a single dataset from the NetCDF
        Subset Service for Daymet data

    """
    params_list = []

    if (end_time.year - start_time.year) == 0:
        params_list.append(DaymetDownloadParameters(year=start_time.year, variable=variable, name=name,
                                                    west=minx, south=miny, east=maxx, north=maxy, start_time=start_time,
                                                    end_time=end_time))
        return params_list
    elif (end_time.year - start_time.year) >= 1:
        start_year_start_time = start_time
        start_year_end_time = datetime.datetime.strptime("{}-12-31T12:00:00".format(start_time.year),
                                                         "%Y-%m-%dT%H:%M:%S")
        start_year_params = DaymetDownloadParameters(year=start_time.year, variable=variable,
                                                     name=name, west=minx, south=miny, east=maxx,
                                                     north=maxy, start_time=start_year_start_time,
                                                     end_time=start_year_end_time)

        params_list.append(start_year_params)

        for year in range(start_time.year + 1, end_time.year):
            current_start = datetime.datetime.strptime("{}-01-01T12:00:00".format(year), "%Y-%m-%dT%H:%M:%S")
            current_end = datetime.datetime.strptime("{}-12-31T12:00:00".format(year), "%Y-%m-%dT%H:%M:%S")
            params_list.append(DaymetDownloadParameters(year=year, variable=variable,
                                                        name=name, west=minx, south=miny, east=maxx,
                                                        north=maxy, start_time=current_start, end_time=current_end))

        end_year_start_time = datetime.datetime.strptime("{}-01-01T12:00:00".format(end_time.year),
                                                         "%Y-%m-%dT%H:%M:%S")
        end_year_end_time = end_time
        end_year_params = DaymetDownloadParameters(year=end_time.year, variable=variable,
                                                   name=name, west=minx, south=miny, east=maxx,
                                                   north=maxy, start_time=end_year_start_time,
                                                   end_time=end_year_end_time)
        params_list.append(end_year_params)
    else:
        raise ValueError("Can't create download params for negative timespan {} to {}"
                         .format(start_time, end_time))
    return params_list


def download_daymet(params: DaymetDownloadParameters, version: str, timeout: int, outpath: str = None):
    """
    Downloads a certain dataset in NetCDF format from the NetCDF Subset Service for Daymet data by using the given
    DaymetDownloadParameters.

    Parameters
    ----------
    params: DaymetDownloadParameters
        Parameters used for a single request
    version: str
        Version of the Daymet dataset (supported: v3, v4)
    outpath: str
        Path to store the downloaded NetCDF file. If None, the downloaded dataset will not be stored within a file
        but returned as xarray.Dataset

    """
    r = req.get(params.get_request_url(version), params=params.get_params_dict(), timeout=timeout)
    if r.status_code != req.codes.ok:
        r.raise_for_status()
    if outpath is not None:
        out_dir = "{}/{}".format(outpath, params.name)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        f = open("{}/{}_{}".format(out_dir, params.name, params.get_file_name(version)), "wb")
        f.write(r.content)
        f.close()
        logger.info(f"Stored Daymet data into file {f.name}")
    else:
        with xr.open_dataset(BytesIO(r.content), engine="h5netcdf") as ds:
            return ds


def download_and_merge_multiple_daymet_datasets(feature: str, params_list: list, outpath: str, version: str, timeout: int):
    """
    Downloads multiple datasets in NetCDF format from the NetCDF Subset Service for Daymet data for a single feature
    using the given list of DaymetDownloadParameters. The single NetCDF datasets will be concatenated and stored within
    a single file.

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
        logger.info(f"Downloading Daymet file {counter} of {len(params_list)}: {params.get_file_name(version)}"
                    f" for feature {params.name}")
        try:
            ds = download_daymet(params, version, timeout)
            ds_list.append(ds)
        except req.exceptions.HTTPError as ex:
            logger.warning(f"Failed downloading Daymet file {params.get_file_name(version)}"
                           f" for feature {params.name}. Cause: {ex}")
        except req.exceptions.Timeout as ex:
            logger.warning(f"Timeout during downloading Daymet file {params.get_file_name(version)}"
                           f" for feature {params.name}. Cause: {ex}")
    result = xr.concat(ds_list, dim="time").sortby("time")
    if version == "v3":
        path = "{}/{}_daymet_v3_{}_na.nc4"
    elif version == "v4":
        path = "{}/{}_daymet_v4_daily_na_{}.nc4"
    else:
        path = "{}/{}_daymet_v4_daily_na_{}.nc4"
    result.to_netcdf(path.format(outpath, feature, params.variable))
    logger.info(f"Stored Daymet files into file {path.format(outpath, feature, params.variable)}")
    logger.info(f"Finished downloading {counter} Daymet files")


def download_multiple_daymet_datasets(params_list: list, outpath: str, version: str, timeout: int):
    """
    Downloads multiple datasets in NetCDF format from the NetCDF Subset Service for Daymet data for a single feature
    using the given list of DaymetDownloadParameters.

    Parameters
    ----------
    params_list: list
        List of request parameters
    outpath: str
        Path to store the datasets within a single NetCDF file
    version: str
        Version of the Daymet dataset (supported: v3, v4)

    """
    counter = 0
    for params in params_list:
        counter += 1
        logger.info(f"Downloading Daymet file {counter} of {len(params_list)}: "
                    f"{params.get_file_name(version)} for config/feature {params.name}")
        try:
            download_daymet(params, version, timeout, outpath)
        except req.exceptions.HTTPError as ex:
            logger.warning(f"Failed downloading Daymet file {params.get_file_name(version)}"
                           f" for config/feature {params.name}. Cause: {ex}")
        except req.exceptions.ConnectionError as ex:
            logger.warning(f"Connection failed when trying to download Daymet file {params.get_file_name(version)}"
                           f" for config/feature {params.name}. Cause: {ex}")
        except req.exceptions.Timeout as ex:
            logger.warning(f"Timeout during downloading Daymet file {params.get_file_name(version)}"
                           f" for config/feature {params.name}. Cause: {ex}")
