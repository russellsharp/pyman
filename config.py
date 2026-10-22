import os
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = (
    Path(os.path.dirname(sys.executable))
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    else next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
)

TEST_ROOT: Final[Path] = PROJECT_ROOT / "test/"

TEST_MATRIAL_PATH: Final[Path] = TEST_ROOT / "material/"

TEST_SCRAP_PATH: Final[Path] = TEST_ROOT / "scrap"

CONFIG_PATH: Final[Path] = PROJECT_ROOT / "config.json"
