from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field


class Configuration(BaseModel):
    indention: int = 2
    default_directories: list[Path] = Field(default_factory=list[Path])
    max_depth: int = 2

    def to_json(self) -> str:
        return self.model_dump_json(indent=self.indention)

    @classmethod
    def load_json(cls, path: Path) -> Self:
        if not path.exists():
            return cls()
        return cls.model_validate_json(path.read_text())
