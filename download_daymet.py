import sys
import warnings

import requests as req
from scripts import daymet


def main():
    if len(sys.argv) != 2:
        raise ValueError("Missing argument for config file path!")
    config_path = sys.argv[1]
    config = daymet.read_daymet_download_config(config_path)
    if config.ids is None:
        print("Start downloading Daymet files for all features stored in {} within timeframe {} to {}"
              .format(config.geo_file, config.start_time, config.end_time))
    else:
        print("Start downloading Daymet files for features {} stored in {} within timeframe {} to {}"
              .format(config.ids, config.geo_file, config.start_time, config.end_time))
    params_list = daymet.create_daymet_download_params(config)
    if config.single_file_storage:
        for feature_id in config.ids:
            params = list(filter(lambda x: x.feature_id == feature_id, params_list))
            daymet.download_and_merge_multiple_daymet_datasets(feature_id, params, config.output_dir, config.version)
    else:
        counter = 0
        for params in params_list:
            counter += 1
            print("Downloading Daymet file {} from {}: {} for feature {}"
                  .format(counter, len(params_list), params.get_file_name(config.version), params.feature_id), end="\r")
            try:
                daymet.download_daymet(params, config.output_dir, config.version)
            except req.exceptions.HTTPError as ex:
                print("WARNING: Failed downloading Daymet file {} for feature {}. Cause: {}".format(
                    params.get_file_name(config.version), params.feature_id, ex))
    print("\nFinished downloading {} Daymet file(s)".format(len(params_list)))


if __name__ == "__main__":
    main()
