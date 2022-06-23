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
### Download Daymet data
In order to run the _download_daymet.py_ script, you have to provide a configuration file which controls the download
process. You'll find an exemplary config files inside _./config_ which you can use as starting point. The download script
supports two modes: download for multiple areas based on a geo file and download for a fixed bounding box.

Prepare a config file as stated above and run the `download_daymet.py` script with the path to the config file as
only positional argument e.g., `python download_daymet.py ./config/download-config.yml`.

The script will download Daymet datasets via NetCDF Subset Service (NCSS) for each geospatial object present in the
provided geo file and indicated by the ids in the config file. To do so, the bounding box of each geospatial object
as well as the specified variable and timeframe will be used as request parameters.

#### Geo file download
This mode takes the polygonal geometries for different basins or other geospatial features from a geo file and downloads
Daymet data for each of the geometries based on its bounding box. Daymet files will be downloaded for a certain variable.

| Config parameter    | Description                                                                                                                                                                                                                                                         |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _geo.file_          | Path to a file that contains geospatial data. The file must be in a data format that can be read by GeoPandas and should contain polygon geometries with WGS84 coordinates, which will be used for requesting Daymet data.                                          |
| _geo.idCol_         | Name of the column that contains unique identifiers for the geospatial objects.                                                                                                                                                                                     |
| _geo.ids_           | IDs of the geospatial objects used for requesting Daymet data. If `None`, all geospatial objects from the _geo.file_ will be considered.                                                                                                                            |
| _readTimeout_       | Sets a read timeout for the download.                                                                                                                                                                                                                               |
| _singleFileStorage_ | For `true` the downloaded yearly Daymet datasets will be concatenated by time dimension and stored within a single file for each geospatial object. For `false` the downloaded yearly Daymet datasets will be stored within separate files foreach object and year. |
| _timeFrame_         | `startTime` and `endTime` in UTC time for requesting Daymet data.                                                                                                                                                                                                   |
| _outputDir_         | Path to the output directory directory. Downloaded datasets will be stored here.                                                                                                                                                                                    |
| _variable_          | Data variable that should be included in the downloaded Daymet datasets.                                                                                                                                                                                            |
| _version_           | Version of the Daymet dataset to be downloaded.                                                                                                                                                                                                                     |

#### Bbox file download
This mode takes a bbox parameter that will be directly used for download Daymet files for the specified variable.

| Config parameter    | Description                                                                                                                                                                                                                                                         |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _bbox_              | A static bbox used for downloading Daymet files. Format: [minLon, minLat, maxLon, maxLat] (e.g. [-73.73, 40.93, -73.72, 40.94])                                                                                                                                     |
| _readTimeout_       | Sets a read timeout for the download.                                                                                                                                                                                                                               |
| _singleFileStorage_ | For `true` the downloaded yearly Daymet datasets will be concatenated by time dimension and stored within a single file for each geospatial object. For `false` the downloaded yearly Daymet datasets will be stored within separate files foreach object and year. |
| _timeFrame_         | `startTime` and `endTime` in UTC time for requesting Daymet data.                                                                                                                                                                                                   |
| _outputDir_         | Path to the output directory directory. Downloaded datasets will be stored here.                                                                                                                                                                                    |
| _variable_          | Data variable that should be included in the downloaded Daymet datasets.                                                                                                                                                                                            |
| _version_           | Version of the Daymet dataset to be downloaded.                                                                                                                                                                                                                     |


### Processing Daymet data
This repo also comes with some processing routines. Up to now, it supports combining, clipping and aggregating Daymet
NetCDF files. You can control processing Daymet data via the _process_daymet.py_ script by providing a configuration
file. You'll find different exemplary files inside _./config_ which you can use as starting point.  

Prepare a config file as stated above and run the `process_daymet.py` script with the path to the config file as
positional argument followed by a certain operation that should be applied to the Daymet files:
`python process_daymet.py {operation} ./config/processing-config.yml`.

#### Combining Daymet data
The `combine` discovers multiple Daymet NetCDF files which have been downloaded with the _download.py_ script and merges
those files that refer to the same basin. NetCDF files with the same basin ID as file name prefix will be handled as 
related files and merged. 

In order to discover all relevant files, folder structure and file naming must follow the conventions mentioned below:
* `{data_dir}/{variable}/{id}/{id}_daymet_v4_daily_na_{variable}_*.nc.`
* `{data_dir}/{variable}/{id}/{id}_daymet_v3_{variable}_*_na.nc4`  
These patterns follow the naming style for single downloaded files as a result of the _download.py_ script.

| Config parameter                | Description                                                                                                                                                                                                                    |
|---------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _dataDir_                       | Path of the data directory which contains the Daymet NetCDF files. Only files which are stored according to a certain folder structure (you'll find an example below) within this directory will be considered for processing. |
| _outputDir_                     | Path to the output directory directory. Processing results will be stored here.                                                                                                                                                |
| _ids_                           | Identifier used to determine, which Daymet files should be considered for processing. Leave empty, if all Daymet files inside the `dataDir` should be considered.                                                              |
| _outputFormat_                  | Format for storing the results. Supporter: netcdf, zarr                                                                                                                                                                        |
| _version_                       | Version of the Daymet datasets.                                                                                                                                                                                                |
| _operationParameters.variables_ | Only a subset of the available Daymet datasets containing these variables will be considered for processing.                                                                                                                   |
  
### Clipping Daymet data
The `clip` operation clips Daymet data for given polygonal geometries stored in a geo file.

In order to discover all relevant files, folder structure and file naming must follow the conventions mentioned below:
* `{data_dir}/{id}_daymet_v4_daily_na.nc`
* `{data_dir}/{id}_daymet_v3_na.nc4`  
These patterns follow the naming style for stored results of the _combine_ operation.

| Config parameter               | Description                                                                                                                                                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _dataDir_                      | Path of the data directory which contains the Daymet NetCDF files. Only files which are stored according to a certain folder structure (you'll find an example below) within this directory will be considered for processing. |
| _outputDir_                    | Path to the output directory directory. Processing results will be stored here.                                                                                                                                                |
| _ids_                          | Identifier used to determine, which Daymet files should be considered for processing. Leave empty, if all Daymet files inside the `dataDir` should be considered.                                                              |
| _outputFormat_                 | Format for storing the results. Supporter: netcdf, zarr                                                                                                                                                                        |
| _version_                      | Version of the Daymet datasets.                                                                                                                                                                                                |
| _operationParameters.geomPath_ | Path to the file that contains polygonal geometries.                                                                                                                                                                           |
| _operationParameters.idCol_    | Name of the ID column within the geo file.                                                                                                                                                                                     |

### Aggregate Daymet data
The `aggregate` operation calculates the _mean_, _min_ or _max_ for Daymet data across the combined 'x' and 'y' dimension.

In order to discover all relevant files, folder structure and file naming must follow the conventions mentioned below:
* `{data_dir}/{id}_daymet_v4_daily_na.nc`
* `{data_dir}/{id}_daymet_v3_na.nc4`  
These patterns follow the naming style for stored results of the _combine_ operation.

| Config parameter                      | Description                                                                                                                                                                                                                    |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| _dataDir_                             | Path of the data directory which contains the Daymet NetCDF files. Only files which are stored according to a certain folder structure (you'll find an example below) within this directory will be considered for processing. |
| _outputDir_                           | Path to the output directory directory. Processing results will be stored here.                                                                                                                                                |
| _ids_                                 | Identifier used to determine, which Daymet files should be considered for processing. Leave empty, if all Daymet files inside the `dataDir` should be considered.                                                              |
| _outputFormat_                        | Format for storing the results. Supporter: netcdf, zarr                                                                                                                                                                        |
| _version_                             | Version of the Daymet datasets.                                                                                                                                                                                                |
| _operationParameters.aggregationMode_ | Defines which aggregation operation should be performed. Supported: mean, min, max                                                                                                                                             |

## References
Thornton, P.E., M.M. Thornton, B.W. Mayer, Y. Wei, R. Devarakonda, R.S. Vose, and R.B. Cook. 2016. _Daymet: Daily Surface
Weather Data on a 1-km Grid for North America, Version 3_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1328

Thornton, M.M., R. Shrestha, Y. Wei, P.E. Thornton, S. Kao, and B.E. Wilson. 2020. _Daymet: Daily Surface Weather Data 
on a 1-km Grid for North America, Version 4_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1840

Newman, A., Sampson, K., Clark, M. P., Bock, A., Viger, R. J., Blodgett, D. (2014). _A large-sample
watershed-scalehydrometeorological dataset for the contiguous USA_. Boulder, CO: UCAR/NCAR. https://dx.doi.org/10.5065/D6MW2F4D
