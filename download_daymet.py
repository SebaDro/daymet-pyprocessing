import logging
import logging.config
import yaml
from scripts import download
import argparse


def main():
    parser = argparse.ArgumentParser(description='Download some Daymet files.')
    parser.add_argument('config', type=str, help="Path to a config file that controls the download process")
    args = parser.parse_args()

    with open("./config/logging.yml", "r") as stream:
        log_config = yaml.load(stream, Loader=yaml.FullLoader)
        logging.config.dictConfig(log_config)

    config_path = args.config
    config = download.read_daymet_download_config(config_path)
    if isinstance(config, download.DaymetDownloadGeofileConfig):
        if config is None:
            raise SystemExit("Could not read configuration file.")
        if config.ids is None:
            logging.info(f"Start downloading Daymet files for all features stored in {config.geo_file} within timeframe"
                         f" {config.start_time} to {config.end_time}")
        else:
            logging.info(f"Start downloading Daymet files for features {config.ids} stored in {config.geo_file} within"
                         f" timeframe {config.start_time} to {config.end_time}")
        params_list = download.create_daymet_download_params_from_config(config)
        if config.single_file_storage:
            for feature_id in config.ids:
                params = list(filter(lambda x: x.name == feature_id, params_list))
                download.download_and_merge_multiple_daymet_datasets(feature_id, params, config.output_dir, config.version)
        else:
            download.download_multiple_daymet_datasets(params_list, config.output_dir, config.version)
        logging.info(f"Finished downloading {len(params_list)} Daymet file(s)")
    elif isinstance(config, download.DaymetDownloadBboxConfig):
        if config is None:
            raise SystemExit("Could not read configuration file.")
        logging.info(f"Start downloading Daymet files for bbox {config.bbox} within"
                     f" timeframe {config.start_time} to {config.end_time}")
        params_list = download.create_daymet_download_params_from_config(config)
        download.download_multiple_daymet_datasets(params_list, config.output_dir, config.version)
    else:
        raise SystemExit("Unknown config.")


if __name__ == "__main__":
    main()
