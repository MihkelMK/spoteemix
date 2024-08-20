import json
import os
from pathlib import Path

import click

APP_NAME = "spoteemix"


def dict_to_json(json_data, indent=2, sort_keys=False):
    # Load new defaults if changed in a config file
    context = click.get_current_context()
    if context.obj["JSON"]:
        indent = context.obj["JSON"]["indent"]
        sort_keys = context.obj["JSON"]["sort_keys"]

    return json.dumps(json_data, indent=indent, sort_keys=sort_keys)


def read_config(file, current_config):
    new_config = {}

    with file.open() as conf_file:
        new_config = json.load(conf_file)

    # Merge config dictionaries, prefer new values
    return current_config | new_config


def load_configs():
    global_cfg = Path(os.path.join(click.get_app_dir(APP_NAME), "config.json"))

    config = {}

    if global_cfg.is_file():
        config = read_config(global_cfg, config)

    return config
