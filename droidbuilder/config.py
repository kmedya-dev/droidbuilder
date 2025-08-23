import toml
import os

CONFIG_FILE = "droidbuilder.toml"

def load_config(path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return toml.load(f)
    return {}

def save_config(config, path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    with open(config_path, "w") as f:
        toml.dump(config, f)
