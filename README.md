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
### Config
In order to run the _download_daymet.py_ script, you have to provide a configuration file which controls the download
process. You'll find an exemplary config file inside _./config_ which you can use as starting point.  

**geo.file:**  
Path to a file that contains geospatial data. The file must be in a data format that can be read by GeoPandas and
should contain polygon geometries with WGS84 coordinates, which will be used for requesting Daymet data.  

**geo.idCol**:  
Name of the column that contains unique identfiers for the geospatial objects.  

**geo.ids:**  
IDs of the geospatial objects used for requesting Daymet data

**singleFileStorage:**  
For `true` the downloaded yearly Daymet datasets will be concatenated by time dimension and stored within a single file
for each geospatial object. For `false` the downloaded yearly Daymet datasets will be stored within separate files for
each object and year.  

**timeFrame:**  
`startTime` and `endTime` for requesting Daymet data

**outputDir:**  
Downloaded datasets will be stored within this directory

**variable:**  
Data variable that should be included in the downloaded Daymet datasets

**version:**  
Daymet Version to request data for

### Download Daymet data
Prepare a config file as stated above and run the `download_daymet.py` script with the path to the config file as
only positional argument e.g., `python download_daymet.py ./config/download-config.yml`.

The script will download Daymet datasets via NetCDF Subset Service (NCSS) for each geospatial object present in the
provided geo file and indicated by the ids in the config file. To do so, the bounding box of each geospatial object
as well as the specified variable and timeframe will be used as request parameters.  

## References
Thornton, P.E., M.M. Thornton, B.W. Mayer, Y. Wei, R. Devarakonda, R.S. Vose, and R.B. Cook. 2016. _Daymet: Daily Surface
Weather Data on a 1-km Grid for North America, Version 3_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1328

Thornton, M.M., R. Shrestha, Y. Wei, P.E. Thornton, S. Kao, and B.E. Wilson. 2020. _Daymet: Daily Surface Weather Data 
on a 1-km Grid for North America, Version 4_. ORNL DAAC, Oak Ridge, Tennessee, USA. https://doi.org/10.3334/ORNLDAAC/1840

Newman, A., Sampson, K., Clark, M. P., Bock, A., Viger, R. J., Blodgett, D. (2014). _A large-sample
watershed-scalehydrometeorological dataset for the contiguous USA_. Boulder, CO: UCAR/NCAR. https://dx.doi.org/10.5065/D6MW2F4D
