from pathlib import Path

from packaging.version import Version


class PythonVersion:
    def __init__(self, version: str | Version, path: Path):
        self.Version: Version = (
            version if isinstance(version, Version) else Version(version)
        )
        self.Path: Path = path

    def __repr__(self) -> str:
        return f"{self.Version} - {self.Path}"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PythonVersion):
            return False  # type: ignore
        return self.Version == other.Version and self.Path == other.Path

    def __hash__(self):
        return hash((self.Version, self.Path))
