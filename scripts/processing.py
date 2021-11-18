import yaml
import xarray as xr
import os
import logging

logger = logging.getLogger(__name__)


class DaymetProcessingConfig:
    def __init__(self, geo_file: str, data_dir: str, ids: list, output_dir: str,  variables: list, version: str):
        self.__geo_file = geo_file
        self.__data_dir = data_dir
        self.__ids = ids
        self.__output_dir = output_dir
        self.__variables = variables
        self.__version = version

    @property
    def data_dir(self):
        return self.__data_dir

    @property
    def geo_file(self):
        return self.__geo_file

    @property
    def ids(self):
        return self.__ids

    @property
    def output_dir(self):
        return self.__output_dir

    @property
    def variables(self):
        return self.__variables

    @property
    def version(self):
        return self.__version


def read_daymet_preprocessing_config(path: str) -> DaymetProcessingConfig:
    """
    Reads configuration parameters from a *.yml file for processing Damet files.

    Parameters
    ----------
    path: str
        Path to the configuration file

    Returns
    -------
    DaymetProcessingConfig
        Object containing config parameters controlling the processing of Daymet data

    """
    with open(path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            return DaymetProcessingConfig(config["geoFile"], config["dataDir"], config["ids"], config["outputDir"],
                                          config["variables"], config["version"])
        except yaml.YAMLError as ex:
            print("Error reading config file {}".format(ex))
        except KeyError as ex:
            print("Missing config parameter: {}".format(ex))


def combine_multiple_daymet_files(files: list, outpath: str, variable: str, feature_id: str, version: str):
    path = os.path.join(outpath, get_file_name(variable, feature_id, version))
    with xr.open_mfdataset(files) as xds:
        xds.to_netcdf(path)


def get_file_name(variable: str, feature_id: str, version: str):
    if version == "v3":
        return get_v3_file_name(variable, feature_id)
    elif version == "v4":
        return get_v4_file_name(variable, feature_id)
    else:
        logger.warning(f"Unsupported version {version}. Returned v4 file name.")
        return get_v4_file_name(variable, feature_id)


def get_v3_file_name(variable: str, feature_id: str):
    return "{}_daymet_v3_{}_na.nc4".format(feature_id, variable)


def get_v4_file_name(variable: str, feature_id: str):
    return "{}_daymet_v4_daily_na_{}.nc".format(feature_id, variable)
