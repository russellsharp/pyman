from collections.abc import Generator
from pathlib import Path

import pytest
from russell.common import setup_logger
from russell.utilities.utilities import safe_file

from config import TEST_SCRAP_PATH
from src.configuration import Configuration

logger = setup_logger(__name__)

type YieldFixture[T] = Generator[T]


@pytest.fixture(scope="module", autouse=True)
def _module_setup_teardown(fixture_example_config_path: Path) -> YieldFixture[None]:
    yield None
    # fixture_example_config_path.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def fixture_example_config_path() -> Path:
    return TEST_SCRAP_PATH / "test_config.json"


@pytest.fixture
def fixture_example_configuration() -> Configuration:
    return Configuration(default_directories=[Path("C:\\")], max_depth=3)


@pytest.fixture
def fixture_reference_config_file(
    fixture_example_config_path: Path, fixture_example_configuration: Configuration
) -> YieldFixture[Path]:
    with safe_file(fixture_example_config_path, "w") as reference_config_file:
        reference_config_file.write(fixture_example_configuration.to_json())
    yield fixture_example_config_path
    logger.info(f"delete test config file {fixture_example_config_path}")
    fixture_example_config_path.unlink(missing_ok=True)


def test_load_config(
    fixture_example_configuration: Configuration, fixture_reference_config_file: Path
):
    loaded_config = Configuration.load_json(fixture_reference_config_file)
    assert loaded_config == fixture_example_configuration


def test_save_config(
    fixture_example_configuration: Configuration, fixture_example_config_path: Path
) -> None:
    with safe_file(fixture_example_config_path, "w") as config_file:
        config_file.write(fixture_example_configuration.to_json())
    written_config = Configuration.load_json(fixture_example_config_path)
    assert fixture_example_configuration == written_config
