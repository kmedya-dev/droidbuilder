import toml
import os
from .cli_logger import logger

CONFIG_FILE = "droidbuilder.toml"

def load_config(path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    logger.info(f"Loading configuration from {config_path}")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return toml.load(f)
    return {}

def save_config(config, path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    logger.info(f"Saving configuration to {config_path}")
    with open(config_path, "w") as f:
        toml.dump(config, f)