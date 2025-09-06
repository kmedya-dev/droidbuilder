import toml
import os
from .cli_logger import logger

CONFIG_FILE = "droidbuilder.toml"

def load_config(path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    logger.info(f"Loading configuration from {config_path}")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return toml.load(f)
        except toml.TomlDecodeError as e:
            logger.error(f"Error decoding TOML file at {config_path}: {e}")
            logger.info("Please check the file's format for syntax errors.")
            return None # Indicate failure
        except IOError as e:
            logger.error(f"Error reading configuration file at {config_path}: {e}")
            logger.info("Please check file permissions.")
            return None # Indicate failure
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading configuration from {config_path}: {e}")
            logger.exception(*sys.exc_info())
            return None # Indicate failure
    return {} # Return empty dict if file doesn't exist

def save_config(config, path="."):
    config_path = os.path.join(path, CONFIG_FILE)
    logger.info(f"Saving configuration to {config_path}")
    try:
        with open(config_path, "w") as f:
            toml.dump(config, f)
        return True
    except IOError as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        logger.info("Please check file permissions and ensure the directory is writable.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while saving configuration to {config_path}: {e}")
        logger.exception(*sys.exc_info())
        return False