import xarray
import yaml
import xarray as xr
import os
import logging
import geopandas as gpd

from dask.diagnostics import ProgressBar
from typing import Tuple

from daymetpyprocessing import ioutils

daymet_proj_str = "+proj = lcc + lat_1 = 25 + lat_2 = 60 + lat_0 = 42.5 + lon_0 = -100 + x_0 = 0 + y_0 = 0 + ellps = WGS84 + units = m + no_defs"
logger = logging.getLogger(__name__)


class DaymetProcessingConfig:
    """
    Configuration parameters for controlling Daymet processing operations
    """

    def __init__(self, data_dir: str, logging_config: str,  output_dir: str, version: str, output_format: str, ids: list = None,
                 params: dict = None):
        """
        Creates a new DaymetProcessingConfig instance

        Parameters
        ----------
        data_dir: str
            Data directory that contains Daymet NetCDF files to process
        logging_config: str
            Path to a logging configuration file
        output_dir: str
            Directory, which will be used for storing the results
        version: str
            Version of the Daymet files ('v3' or 'v4')
        output_format: str
            Format of the resulting files (Supported: 'netcdf', 'zarr')
        ids: List of str
            List of IDs that are part of the Daymet file names and define which files to process
        params: dict
            Operation specific parameters
        """
        self.__data_dir = data_dir
        self.__logging_config = logging_config
        self.__output_dir = output_dir
        self.__version = version
        self.__output_format = output_format
        self.__ids = ids
        self.__params = params

    @property
    def data_dir(self):
        return self.__data_dir

    @property
    def logging_config(self):
        return self.__logging_config

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
    def version(self):
        return self.__version

    @property
    def params(self):
        return self.__params

    @property
    def output_format(self):
        return self.__output_format


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
            return DaymetProcessingConfig(config["dataDir"], config["loggingConfig"], config["outputDir"],
                                          config["version"], config["outputFormat"], ids, params)
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
    variables = config.params["variables"]
    if config.ids is None:
        logger.info(f"Discovering all Daymet files for variables {variables}")
        file_dict = ioutils.discover_yearly_daymet_files(config.data_dir, variables, config.version)
        for key in file_dict:
            files = file_dict[key]
            logger.info(f"Successfully discovered {len(files)} files for id {key}. Start combining ...")
            path, meta_dict = combine_multiple_daymet_files(files, config.output_dir, config.output_format, key,
                                                            config.version)
            log_metadata(variables, meta_dict)
            logger.info(f"Successfully combined and stored {len(files)} files in file {path} for id {key}.")
    else:
        for key in config.ids:
            logger.info(f"Discovering Daymet files for feature '{key}' and variables {variables}")
            files = ioutils.discover_yearly_daymet_files_for_id_and_variable(config.data_dir, key, variables, config.version)
            logger.info(f"Successfully discovered {len(files)} files for id {key}. Start combining ...")
            path, meta_dict = combine_multiple_daymet_files(files, config.output_dir, config.output_format, key,
                                                            config.version)
            log_metadata(variables, meta_dict)
            logger.info(f"Successfully combined and stored {len(files)} files in file {path} for id {key}.")


def clip(config: DaymetProcessingConfig):
    """
    Runs the clipping operation for various Daymet NetCDF files in accordance to the specified configuration

    Parameters
    ----------
    config: DaymetProcessingConfig
        Holds configuration parameters that manage the processing flow

    """
    geom_path = config.params["geomPath"]
    id_col = config.params["idCol"]

    res_postfix = None
    if config.data_dir == config.output_dir:
        logger.warning(f"Input data directory and output directory are the same. Resulting files will be postfixed with"
                       f" '_clipped'")
        res_postfix = "_clipped"

    features = gpd.read_file(geom_path)
    features = features.to_crs(daymet_proj_str)

    features[id_col] = features[id_col].astype(str)
    basin_ids = features[id_col].tolist()
    basin_ids = ["0" + i if len(i) < 8 else i for i in basin_ids]
    features[id_col] = basin_ids

    if config.ids is not None:
        basin_ids = config.ids

    for basin_id in basin_ids:
        logger.info(f"Discovering Daymet files for ID '{basin_id}'")
        try:
            xds_path = ioutils.discover_daymet_file_for_id(config.data_dir, basin_id, config.version)
            logger.info(f"Successfully discovered file {xds_path} files for ID '{basin_id}'.")
            feature = features[features[id_col] == basin_id]
            if feature.empty:
                logger.error(f"No feature available for id '{basin_id}'. Clipping will be skipped.")
            else:
                logger.info("Start clipping...")
                if res_postfix is None:
                    out_path = os.path.join(config.output_dir, os.path.basename(xds_path))
                else:
                    split_name = os.path.basename(xds_path).split(".")
                    out_path = os.path.join(config.output_dir, f"{split_name[0]}_{res_postfix}.{split_name[1]}")

                with xr.open_dataset(xds_path, decode_coords="all") as xds:
                    xds = xds.assign_coords(y=xds.y * 10 ** 3, x=xds.x * 10 ** 3)
                    xds["prcp"] = xds.prcp.assign_attrs(units='mm/day')
                    xds["x"] = xds.x.assign_attrs(units='m')
                    xds["y"] = xds.y.assign_attrs(units='m')

                    xds_clipped = xds.rio.clip(feature.geometry)
                    save(xds_clipped, out_path, config.output_format)
                    logger.info(f"Successfully saved result in file {out_path}")
        except FileNotFoundError as e:
            logger.error(f"Skip clipping for basin {basin_id}: {e}")


def aggregate(config: DaymetProcessingConfig):
    """
    Runs the aggregation operation for various Daymet NetCDF files in accordance to the specified configuration

    Parameters
    ----------
    config: DaymetProcessingConfig
        Holds configuration parameters that manage the processing flow

    """
    aggregation_mode = config.params["aggregationMode"]
    res_postfix = None
    if config.data_dir == config.output_dir:
        logger.warning(f"Input data directory and output directory are the same. Resulting files will be postfixed with"
                       f" '{aggregation_mode}'")
        res_postfix = aggregation_mode

    file_paths = []
    if config.ids is not None:
        logger.info(f"Discovering Daymet files for IDs {config.ids} within directory '{config.data_dir}'")
        for basin_id in config.ids:
            try:
                file = ioutils.discover_daymet_file_for_id(config.data_dir, basin_id, config.version)
                file_paths.append(file)
            except FileNotFoundError as e:
                logger.error(f"Cannot calculate aggregation fo basin {basin_id}: {e}")
        logger.info(f"Discovered {len(file_paths)} paths")
    else:
        logger.info(f"Discovering all Daymet files within directory '{config.data_dir}'")
        files = ioutils.discover_daymet_files(config.data_dir, config.version)
        file_paths.extend(files)
        logger.info(f"Discovered {len(file_paths)} paths")

    for path in file_paths:
        with xr.open_dataset(path) as xds:
            logger.info(f"Calculate {aggregation_mode} for file '{path}'.")
            if aggregation_mode == "max":
                xds_aggr = xds.max(dim=["y", "x"])
            elif aggregation_mode == "min":
                xds_aggr = xds.min(dim=["y", "x"])
            elif aggregation_mode == "mean":
                xds_aggr = xds.mean(dim=["y", "x"])
            else:
                raise ValueError(f"Unsupported aggregation mode '{aggregation_mode}'. Supported modes: 'min', 'max', "
                                 f"'mean'.")
        if res_postfix is None:
            out_path = os.path.join(config.output_dir, os.path.basename(path))
        else:
            split_name = os.path.basename(path).split(".")
            out_path = os.path.join(config.output_dir, f"{split_name[0]}_{res_postfix}.{split_name[1]}")
        save(xds_aggr, out_path, config.output_format)
        logger.info(f"Successfully saved result in file {out_path}")


def log_metadata(variables: list, meta_dict: dict):
    """
    Logs some metadata about a xarray.Dataset generated by the check_daymet_files function

    Parameters
    ----------
    variables: list
        Variables that should be contained within the xarray.Datset metadata
    meta_dict: dict
        Dictionary with metadata information about xarray.Dataset

    """
    logger.debug(f"Dataset contains {len(meta_dict)} variables: {list(meta_dict.keys())}")
    for v in variables:
        if v in meta_dict:
            logger.debug(f"Variable '{v}' contains {len(meta_dict[v])} timeseries values from {meta_dict[v][0]} to "
                         f"{meta_dict[v][-1]}")
        else:
            logger.warning(f"Dataset does not contain variable '{v}'.")


def check_daymet_file(xds: xarray.Dataset):
    """
    Check metadata information such as timestamp values for different variable keys of a xarray.Dataset to ensure
    dataset operations haven been executed correctly.

    Parameters
    ----------
    xds: xarray.Dataset
        Dataset that contains Daymet data

    Returns
    -------
        Dictionary with certain metadata information which can be used to validate dataset operations

    """
    variables = list(xds.keys())
    meta_dict = {}
    for v in variables:
        meta_dict[v] = xds.prcp.time.values
    return meta_dict


def combine_multiple_daymet_files(files: list, outpath: str, outformat: str, key: str, version: str) -> Tuple[str, dict]:
    """
    Combines mutliple Daymet NetCDF files into a single one by grouping variables

    Parameters
    ----------
    files: list
        Path to the files that should be combined
    outpath: str
        Storage path for the resulting file
    outformat: str
        Output storage format
    key: str
        A key, which will be used for naming the resulting file
    version: str
        Version of the Daymet files (either v3 or v4)

    Returns
    -------
    (str, dict)
        Path to the resulting file as well as metadata about it

    """
    path = os.path.join(outpath, get_file_name(key, version, outformat))
    with xr.open_mfdataset(files) as xds:
        save(xds, outpath, outformat)
        meta_dict = check_daymet_file(xds)
        return path, meta_dict


def save(xds, path, outformat):
    if outformat == "netcdf":
        save_as_netcdf(xds, path)
    elif outformat == "zarr":
        save_as_zarr(xds, path)
    else:
        logger.warning(f"Unsupported output format '{outformat}'. Combined dataset will be stored as NetCDF.")
        save_as_netcdf(xds, path)


def save_as_netcdf(xds: xarray.Dataset, path: str):
    """
    Save a xarray.Dataset as NetCDF and prints the progress

    Parameters
    ----------
    xds: xarray.Dataset
        Dataset
    path: str
        Path, which will be used to store the dataset as NetCDF file

    """
    with ProgressBar():
        xds.to_netcdf(path, engine='h5netcdf')


def save_as_zarr(xds, path):
    """
    Save a xarray.Dataset as Zarr and prints the progress

    Parameters
    ----------
    xds: xarray.Dataset
        Dataset
    path: str
        Path, which will be used to store the dataset as Zarr file

    """
    with ProgressBar():
        xds.to_zarr(path)


def get_file_name(file_id: str, version: str, outformat: str):
    """
    Determines the output file name in accordance to a file ID, the Daymet data version and the output format

    Parameters
    ----------
    file_id:
        ID which will be used to prefix the file
    version:
        Daymet version ('v3' or 'v4')
    outformat
        Format of the output

    Returns
    -------
    str
        The resulting file name

    """
    if outformat == "netcdf" and version == "v3":
        return get_nc_v3_file_name(file_id)
    elif outformat == "netcdf" and version == "v4":
        return get_nc_v4_file_name(file_id)
    elif outformat == "zarr":
        return get_zarr_store_name(file_id, version)
    else:
        logger.warning(f"Unsupported version {version}. Returned NetCDF v4 file name.")
        return get_nc_v4_file_name(file_id)


def get_nc_v3_file_name(feature_id: str):
    return f"{feature_id}_daymet_v3_na.nc4"


def get_nc_v4_file_name(feature_id: str):
    return f"{feature_id}_daymet_v4_daily_na.nc"


def get_zarr_store_name(feature_id: str, version: str):
    return f"{feature_id}_daymet_{version}_na.zarr"
