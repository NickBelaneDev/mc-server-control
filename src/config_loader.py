import tomli

from pydantic import ValidationError

from config_models import ServerConfig
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.toml"

_CONFIG_CACHE: ServerConfig | None = None


def load_config() -> ServerConfig:
    """Loads and caches the TOML-config"""
    print("Loading the config.toml...")
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with CONFIG_PATH.open("rb") as f:
        raw = tomli.load(f)

    try:
        _CONFIG_CACHE = ServerConfig(**raw["mc"])
    except ValidationError as e:
        print("Config Validation Error:")
        print(e)
        raise

    print(">> Successfully loaded the config.toml")

    return _CONFIG_CACHE
