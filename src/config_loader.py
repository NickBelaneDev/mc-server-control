import tomli

from pydantic import ValidationError

from .config_models import AppConfig
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.toml"

_CONFIG_CACHE: AppConfig | None = None



def load_config() -> AppConfig:
    """Loads and caches the TOML-config"""
    logger.info("Loading the config.toml...")
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    if not CONFIG_PATH.exists():
        logger.error(f"Config file not found: {CONFIG_PATH}")
        raise FileNotFoundError()

    with CONFIG_PATH.open("rb") as f:
        raw = tomli.load(f)

    try:
        _CONFIG_CACHE = AppConfig(**raw)
    except ValidationError as e:
        logger.exception("Config Validation Error: Something is wrong with your 'config.toml', maybe check all types there?")
        raise

    logger.info(">> Successfully loaded the 'config.toml'.")

    return _CONFIG_CACHE
