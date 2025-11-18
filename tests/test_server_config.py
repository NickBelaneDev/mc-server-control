from src.config_models import ServerConfig
import pytest
from pydantic import ValidationError

def test_config_raises_error_for_invalid_jar():
    with pytest.raises(ValidationError):
        ServerConfig(dir="C:/Users",
                       jar="paper.txt",
                       min_gb=3,
                       max_gb=4,
                       screen_name="test_screen")

def test_config_raises_error_for_empty_jar():
    with pytest.raises(ValidationError):
        ServerConfig(dir="C:/Users",
                       jar="",
                       min_gb=3,
                       max_gb=4,
                       screen_name="test_screen")


def test_config_raises_error_for_none_existing_dir():
    with pytest.raises(ValidationError):
        ServerConfig(dir="C:/Users/loool",
                       jar="paper.jar",
                       min_gb=3,
                       max_gb=4,
                       screen_name="test_screen")

def test_config_ensure_order():
    pass