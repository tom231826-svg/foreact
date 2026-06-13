import pytest

from foreact.config import ConfigError, load_config

from .conftest import path


def test_load_config():
    config = load_config(path("config/fiji.yaml"))
    assert config.country == "Fiji"
    assert config.currency == "FJD"
    assert round(sum(config.weights[key] for key in ("hazard", "vulnerability", "capacity_gap", "access")), 2) == 1.0
    assert len(config.actions) == 4


def test_missing_config_raises():
    with pytest.raises(ConfigError):
        load_config(path("config/nope.yaml"))
