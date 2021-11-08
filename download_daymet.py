import sys
import logging
import logging.config
import yaml
import requests as req
from scripts import daymet

def main():
    with open("./config/logging.yml", "r") as stream:
        log_config = yaml.load(stream, Loader=yaml.FullLoader)
        logging.config.dictConfig(log_config)

    if len(sys.argv) != 2:
        raise ValueError("Missing argument for config file path!")
    config_path = sys.argv[1]
    config = daymet.read_daymet_download_config(config_path)
    if config is None:
        raise SystemExit("Could not read configuration file.")
    if config.ids is None:
        logging.info(f"Start downloading Daymet files for all features stored in {config.geo_file} within timeframe"
                     f" {config.start_time} to {config.end_time}")
    else:
        logging.info(f"Start downloading Daymet files for features {config.ids} stored in {config.geo_file} within"
                     f" timeframe {config.start_time} to {config.end_time}")
    params_list = daymet.create_daymet_download_params(config)
    if config.single_file_storage:
        for feature_id in config.ids:
            params = list(filter(lambda x: x.feature_id == feature_id, params_list))
            daymet.download_and_merge_multiple_daymet_datasets(feature_id, params, config.output_dir, config.version)
    else:
        daymet.download_multiple_daymet_datasets(params_list, config.output_dir, config.version)
    logging.info(f"Finished downloading {len(params_list)} Daymet file(s)")


if __name__ == "__main__":
    main()
