import glob
import os
import logging

logger = logging.getLogger(__name__)


def discover_daymet_files(data_dir: str, variables: list):
    """
    Discovers all Daymet NetCDF files from a root directory for given variables. This method will automatically discover
    all subdirectories inside a variable directory and thus will return a dict with subdirectory name as key
    and all NetCDF file paths belonging to these subdirectories as values. Folder structure and file naming must follow
    the following convention {root_dir}/{variable}/{sub_dir}/{sub_dir}_daymet_v4_daily_na_{variable}_*.nc. Note, that
    {sub_dir} will be discovered automatically.

    Examples: For given variables [var1, var2] the method will discover within the directory {root_dir}/var1/123 all NetCDF
    files with filename 123_daymet_v4_daily_na_var1_*.nc and within the directory {root_dir}/var2/123 all NetCDF files
    with filename 123_daymet_v4_daily_na_var2_*.nc. These file will be stored as values for key 123 within the resulting
    dict. Files and directories that do not follow these conventions will be ignored.

    Parameters
    ----------
    data_dir: str
        Root data dir
    variables: list
        List of variables that should be considered for file discovery

    Returns
    -------
    List
        List of NetCDF file paths

    """
    file_dict = {}
    for variable in variables:
        var_dir = os.path.join(data_dir, variable)
        sub_dir_name_list = os.listdir(var_dir)
        for sub_dir_name in sub_dir_name_list:
            sub_dir = os.path.join(var_dir, sub_dir_name)
            files = glob.glob(f"{sub_dir}/{sub_dir_name}*{variable}*.nc")
            if not files:
                logger.warning(f"No files found in path {data_dir} for variable {variable} and sub directory"
                               f"{sub_dir_name}")
            else:
                if sub_dir_name in file_dict:
                    file_dict[sub_dir_name].extend(files)
                else:
                    file_dict[sub_dir_name] = files
    return file_dict


def discover_daymet_files_for_id_and_variable(root_data_dir: str, id: str, variables: list):
    """
    Discovers all Daymet NetCDF files from a root directory for a given id and specified variables.

    Folder structure and file naming must follow the following convention {root_dir}/{variable}/{id}/{id}_daymet_v4_daily_na_{variable}_*.nc.
    E.g. for given ID 123 and variables [var1, var2] the method will discover within the directory
    {root_dir}/var1/123/ all NetCDF files with filename 123_daymet_v4_daily_na_var1_*.nc and within the directory
    {root_dir}/var2/123 all NetCDF files with filename 123_daymet_v4_daily_na_var2_*.nc. Files and directories that do
    not follow these conventions will be ignored.

    Parameters
    ----------
    root_data_dir: str
        Root data dir
    id: str
        ID which will be used to discover files for the same region in the different variable folders
        variables: Daymet variables to discover the NetCDF files for
    variables: list
        List of variables that should be considered for file discovery

    Returns
    -------
    List
        List of NetCDF file paths

    """
    file_list = []
    for variable in variables:
        data_dir = os.path.join(root_data_dir, variable, id)
        files = glob.glob(f"{data_dir}/{id}*{variable}*.nc")
        if not files:
            logger.warning(f"No files found in path {data_dir} for variable {variable} and basin {id}")
        else:
            file_list.extend(files)
    return file_list


def discover_daymet_file_for_id(root_data_dir: str, id: str):
    """
    Discovers all Daymet NetCDF files from a root directory for a given id.

    Folder structure and file naming must follow the following convention {root_dir}/{id}_daymet_v4_daily_na_*.nc.
    E.g. for given ID 123 the method will discover within the directory {root_dir} all NetCDF files with filename
    123_daymet_v4_daily_na_*.nc. Files and directories that do not follow these conventions will be ignored.

    Parameters
    ----------
    root_data_dir: str
        Root data dir
    id: str
        ID which will be used to discover files for the same region in the different variable folders
        variables: Daymet variables to discover the NetCDF files for

    Returns
    -------
    List
        List of NetCDF file paths

    """
    files = glob.glob(f"{root_data_dir}/{id}_daymet_v4_daily_na.nc")
    if not files or len(files) == 0:
        raise FileNotFoundError(f"No files found in path {root_data_dir} for basin {id}")
    if len(files) > 1:
        logger.warning(f"More than one file was found in path {root_data_dir} for basin {id}. Only first one will be returned.")
    return files[0]


def simple_file_discovery(data_dir: str):
    return os.listdir(data_dir)
