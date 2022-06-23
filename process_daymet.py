import argparse
import logging
import logging.config
import yaml
from scripts import processing


def main():
    parser = argparse.ArgumentParser(description='Process some Daymet files.')
    parser.add_argument('operation', type=str, choices=['merge', 'clip', 'aggregate'], help="Process Daymet files.")
    parser.add_argument('config', type=str, help="Path to a config file that controls the operation process")
    args = parser.parse_args()

    with open("./config/logging.yml", "r") as stream:
        log_config = yaml.load(stream, Loader=yaml.FullLoader)
        logging.config.dictConfig(log_config)

    config = processing.read_daymet_preprocessing_config(args.config)
    if args.operation == "merge":
        if config.ids is None:
            logging.info(f"Start merging Daymet files for all features stored in {config.data_dir}.")
        else:
            logging.info(f"Start merging Daymet files for features {config.ids} stored in {config.data_dir}.")
        processing.combine(config)
        logging.info(f"Finished merging Daymet files.")
    if args.operation == "clip":
        if config.ids is None:
            logging.info(f"Start clipping Daymet files for all features stored in {config.params['geomPath']}.")
        else:
            logging.info(f"Start clipping Daymet files for features {config.ids} stored in {config.data_dir}.")
        processing.clip(config)
        logging.info(f"Finished clipping Daymet files.")
    if args.operation == "aggregate":
        if config.ids is None:
            logging.info(f"Start aggregating Daymet files for all files stored in {config.data_dir}.")
        else:
            logging.info(f"Start aggregating Daymet files for IDs {config.ids} stored in {config.data_dir}.")
        processing.aggregate(config)
        logging.info(f"Finished aggregating Daymet files.")
    else:
        raise SystemExit(f"Unsupported operation '{args.operation}'.")


if __name__ == "__main__":
    main()
