# Daymet PyProcessing
This repository provides various utility scripts for downloading Daymet datasets. Originally, this project was intended
to prepare Daymet surface data for basins of the CAMELS-US dataset. However, the scripts provided in this repo can be
used for any other geospatial objects with polygon geometry.

## Daymet data
Damet data contain gridded estimates of daily weather and climatology parameters at a 1 km x 1 km raster for  
North America, Hawaii, and Puerto Rico. Daymet Version 3 and Version 4 data are provided by ORNL DAAC and can be 
via ORNL DAAC's Thematic Real-time Environmental Distributed Data Services (THREDDS).

## Get started
For installing all required packages you can either use Conda or Pip. Therefore, this repo comes with an
_environment.yml_ and a _requirements.txt_ in this repository, respectively.

## User Guide
### Download config
In order to run the _download_daymet.py_ script, you have to provide a configuration file which controls the download
process. You'll find an exemplary _download-config.yml_ file inside _./config_ which you can use as starting point.  

| Config parameter  | Description                                                                                                                                                                                                                                                         |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _geo.file_          | Path to a file that contains geospatial data. The file must be in a data format that can be read by GeoPandas and should contain polygon geometries with WGS84 coordinates, which will be used for requesting Daymet data.                                          |
| _geo.idCol_         | Name of the column that contains unique identfiers for the geospatial objects.                                                                                                                                                                                      |
| _geo.ids_           | IDs of the geospatial objects used for requesting Daymet data. If `None`, all geospatial objects from the _geo.file_ will be considered.                                                                                                                            |
| _singleFileStorage_ | For `true` the downloaded yearly Daymet datasets will be concatenated by time dimension and stored within a single file for each geospatial object. For `false` the downloaded yearly Daymet datasets will be stored within separate files foreach object and year. |
| _timeFrame_         | `startTime` and `endTime` in UTC time for requesting Daymet data.                                                                                                                                                                                                               |
| _outputDir_         | Path to the output directory directory. Downloaded datasets will be stored here.                                                                                                                                                                                    |
| _variable_          | Data variable that should be included in the downloaded Daymet datasets                                                                                                                                                                                             |
| _version_           | Version of the Daymet dataset to be downloaded                                                                                                                                                                                                                      |

### Processing config
You can also control processing Daymet data via the _process_daymet.py_ script by providing a configuration file. You'll
find an exemplary _processing-config.yml_ file inside _./config_ which you can use as starting point.  

| Config parameter  | Description                                                                                                                                                                                                                                                         |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _ids_                 | Identifier used to determine, which Daymet files should be considered for processing. Leave empty, if all Daymet files inside the `rootDir` should be considered.                                                                                                   |
| _outputDir_           | Path to the output directory directory. Processing results will be stored here.                                                                                                                                                                                     |
| _rootDir_             | Path of the root directory which contains the Daymet NetCDF files. Only files which are stored according to a certain folder structure (you'll find an example below) within this directory will be considered for processing.                                      |
| _variables_           | Only a subset of the available Daymet datasets containing these variables will be considered for processing.                                                                                                                                                        |
| _version_             | Version of the Daymet datasets.                                                                                                                                                                                                                                     |
| _operationParameters_ | Additional parameters which can be used to control the Daymet processing. This is an optional parameter which contains operation specific parameters. For available operations you'll find a list of supported parameters below.                                     | 

**Please note:** For some operations (e.g., merging multiple Daymet files) in order to discover all relevant files, folder
structure and file naming must follow the following convention: `{root_dir}/{variable}/{id}/{id}_daymet_v4_daily_na_{variable}_*.nc.`
E.g. for given variables [var1, var2] the method will discover within the directory `{root_dir}/var1/123/` all NetCDF
files with filename `123_daymet_v4_daily_na_var1_*.nc` and within the directory `{root_dir}/var2/123` all NetCDF files
with filename `123_daymet_v4_daily_na_var2_*.nc`. These file will be stored as values for key 123 within the resulting
dict. Files and directories that do not follow these conventions will be
ignored.

### Download Daymet data
Prepare a config file as stated above and run the `download_daymet.py` script with the path to the config file as
only positional argument e.g., `python download_daymet.py ./config/download-config.yml`.

The script will download Daymet datasets via NetCDF Subset Service (NCSS) for each geospatial object present in the
provided geo file and indicated by the ids in the config file. To do so, the bounding box of each geospatial object
as well as the specified variable and timeframe will be used as request parameters.

### Process Daymet data
Prepare a config file as stated above and run the `process_daymet.py` script with the path to the config file as
positional argument followed by a certain operation that should be applied to the Daymet files:
`python process_daymet.py ./config/processing-config.yml {operation}`. Up to now, the operations below are supported:
- `merge`: Discovers related Daymet files for different variables and years, which will be combined into single NetCDF
  files. For each set of related Daymet files one single NetCDF file will be created. A set of related Daymet files
  comprises all NetCDF files which covers the same geospatial area but differ in the covered timespan and Daymet variables.
  

## References
Thornton, P.E., M.M. Thornton, B.W. Mayer, Y. Wei, R. Devarakonda, R.S. Vose, and R.B. Cook. 2016. _Daymet: Daily Surface
Weather Data on a 1-km Grid for North America, Version 3_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1328

Thornton, M.M., R. Shrestha, Y. Wei, P.E. Thornton, S. Kao, and B.E. Wilson. 2020. _Daymet: Daily Surface Weather Data 
on a 1-km Grid for North America, Version 4_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1840

Newman, A., Sampson, K., Clark, M. P., Bock, A., Viger, R. J., Blodgett, D. (2014). _A large-sample
watershed-scalehydrometeorological dataset for the contiguous USA_. Boulder, CO: UCAR/NCAR. https://dx.doi.org/10.5065/D6MW2F4D
