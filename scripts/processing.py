import yaml
import xarray as xr
import os
import logging
from scripts import ioutils

logger = logging.getLogger(__name__)


class DaymetProcessingConfig:
    def __init__(self, data_dir: str,  output_dir: str,  variables: list, version: str, ids: list = None,
                 params: dict = None):
        self.__data_dir = data_dir
        self.__ids = ids
        self.__output_dir = output_dir
        self.__variables = variables
        self.__version = version
        self.__params = params

    @property
    def data_dir(self):
        return self.__data_dir

    @property
    def ids(self):
        return self.__ids

    @ids.setter
    def ids(self, value):
        self.__ids = value

    @property
    def output_dir(self):
        return self.__output_dir

    @property
    def variables(self):
        return self.__variables

    @property
    def version(self):
        return self.__version

    @property
    def params(self):
        return self.__params


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
            ids = None
            if "ids" in config:
                ids = config["ids"]
            params = None
            if "operationParameters" in config:
                params = config["operationParameters"]
            return DaymetProcessingConfig(config["rootDir"], config["outputDir"], config["variables"], config["version"],
                                          ids, params)
        except yaml.YAMLError as ex:
            print("Error reading config file {}".format(ex))
        except KeyError as ex:
            print("Missing config parameter: {}".format(ex))


def combine(config: DaymetProcessingConfig):
    """
    Runs the combining operation for various Daymet NetCDF files in accordance to the specified configuration

    Parameters
    ----------
    config: DaymetProcessingConfig
        Holds configuration parameters that manage the processing flow

    """
    if config.ids is None:
        logger.info(f"Discovering all Daymet files for variables {config.variables}")
        file_dict = ioutils.discover_daymet_files(config.data_dir, config.variables)
        for key in file_dict:
            files = file_dict[key]
            logger.info(f"Successfully discovered {len(files)} files for id {key}.")
            logger.debug(f"Discovered files: {files}.")
            path = combine_multiple_daymet_files(files, config.output_dir, key, config.version)
            logger.info(f"Successfully combined and stored {len(files)} files in file {path}.")
    else:
        for key in config.ids:
            logger.info(f"Discovering Daymet files for features {config.ids} and variables {config.variables}")
            files = ioutils.discover_daymet_files_for_id(config.data_dir, key, config.variables)
            logger.info(f"Successfully discovered {len(files)} files.")
            logger.debug(f"Discovered files: {files}.")
            path = combine_multiple_daymet_files(files, config.output_dir, key, config.version)
            logger.info(f"Successfully combined and stored {len(files)} files in file {path}.")


def combine_multiple_daymet_files(files: list, outpath: str, key: str, version: str) -> str:
    """
    Combines mutliple Daymet NetCDF files into a single one by grouping variables

    Parameters
    ----------
    files: list
        Path to the files that should be combined
    outpath: str
        Storage path for the resulting file
    key: str
        A key, which will be used for naming the resulting file
    version: str
        Version of the Daymet files (either v3 or v4)

    Returns
    -------
    str
        Path to the resulting file

    """
    path = os.path.join(outpath, get_file_name(key, version))
    with xr.open_mfdataset(files) as xds:
        xds.to_netcdf(path)
    return path


def get_file_name(feature_id: str, version: str):
    if version == "v3":
        return get_v3_file_name(feature_id)
    elif version == "v4":
        return get_v4_file_name(feature_id)
    else:
        logger.warning(f"Unsupported version {version}. Returned v4 file name.")
        return get_v4_file_name(feature_id)


def get_v3_file_name(feature_id: str):
    return "{}_daymet_v3_na.nc4".format(feature_id)


def get_v4_file_name(feature_id: str):
    return "{}_daymet_v4_daily_na.nc".format(feature_id)
