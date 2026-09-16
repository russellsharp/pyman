import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Annotated

import typer

from envvarmanager import IEnvManager, WindowsEnvManager
from pythonversion import PythonVersion

DIRECTORY_DEFAULT_FILE = "default_directories.json"

logging.root.handlers = []
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.propagate = True


class DirectoryDoesNotExist(BaseException):
    def __init__(self, directory: str = "Unknown directory"):
        super().__init__(f"Directory not found: {directory}")


env_manager: IEnvManager = WindowsEnvManager()


class PythonManager:
    @staticmethod
    def list_versions(
        directories: Annotated[
            list[str] | None, typer.Argument(help="Directories to check for python.")
        ] = None,
        file_pattern: Annotated[
            str, typer.Option(help="File name of python executable")
        ] = "python.exe",
    ) -> None:

        directories = directories or []
        directories.extend(PythonManager.__read_python_directory_defaults())
        directories.extend(PythonManager.__read_python_where(file_pattern))
        versions: set[PythonVersion] = set(
            PythonManager.__find_versions(directories, file_pattern)
        )
        current_version = PythonManager.__get_current_version()
        versions.add(current_version)
        for v in versions:
            logger.info(str(v) + "*" if v == current_version else v)
        typer.confirm("Press any key.", abort=True)

    @staticmethod
    def choose_version(
        directories: Annotated[
            list[str] | None, typer.Argument(help="Directories to check for python.")
        ] = None,
        file_pattern: Annotated[
            str, typer.Option(help="File name of python executable")
        ] = "python.exe",
    ) -> None:

        directories = directories or []
        directories.extend(PythonManager.__read_python_directory_defaults())
        directories.extend(PythonManager.__read_python_where(file_pattern))
        logger.info(PythonManager.__read_python_where(file_pattern))
        pythons = PythonManager.__find_versions(directories, file_pattern)
        version_choice: PythonVersion | None = PythonManager.__prompt_versions(pythons)
        if version_choice:
            env_manager.set_python_runtime(version_choice.Path)
            typer.echo(f"Set active python runtime to {version_choice}")
        else:
            typer.echo("Python runtime version unchanged.")
        input(f"Active python runtime version is {env_manager.get_python_runtime()}")

    @staticmethod
    def __find_versions(
        directories: list[str], file_pattern: str = "python.exe"
    ) -> list[PythonVersion]:

        paths: list[Path] = [PythonManager.__resolve_directory(f) for f in directories]

        pythons: list[Path] = []

        for path in paths:
            pythons.extend(PythonManager.__find_file_recurse(path, file_pattern, 2))
        versions: list[PythonVersion] = [
            PythonManager.__get_version(py) for py in pythons
        ]
        return versions

    @staticmethod
    def __prompt_versions(versions: list[PythonVersion]) -> PythonVersion | None:
        current_version = PythonManager.__get_current_version()
        selected = None
        prompt = ""
        for i, v in enumerate(versions):
            prompt += f"\n {v.Path} - {v.Version} ({i})"
            if v == current_version:
                selected = i
                prompt += "*"
        prompt += "\nSelect Version. Default"
        choice: int = 0
        while True:
            choice = typer.prompt(prompt, type=int, default=selected)
            if choice >= 0 and choice < len(versions):
                break

            typer.secho(
                f"Error: Choice must be between 0 and {len(versions) - 1}.",
                fg=typer.colors.RED,
            )
        return versions[choice] if versions[choice] != current_version else None

    @staticmethod
    def __resolve_directory(directory: str) -> Path:
        expanded: Path = Path(directory)
        if "~" in directory:
            expanded = expanded.expanduser()
        if "$" in str(expanded):
            expanded = Path(os.path.expandvars(expanded))

        return expanded.resolve()

    @staticmethod
    def __find_file_recurse(
        directory: Path, file_pattern: str = "python.exe", max_depth: int = 2
    ) -> list[Path]:
        paths: list[Path] = []

        if not directory.exists():
            raise DirectoryDoesNotExist(str(directory))

        base_depth: int = len(directory.parts)

        for root, _, files in directory.walk(top_down=True):
            current_depth = len(root.parts) - base_depth

            if current_depth >= max_depth:
                return paths

            # prepending root directory is necessary
            file_paths = [Path(root / f) for f in files]
            paths.extend(f for f in file_paths if f.is_file() and f.match(file_pattern))
        return paths

    @staticmethod
    def __get_version(python_path: Path | str) -> PythonVersion:
        env_manager.check_privilege()
        python_path = Path(python_path) if isinstance(python_path, str) else python_path
        python_path = (
            python_path / "python.exe" if python_path.is_dir() else python_path
        )
        result: subprocess.CompletedProcess[str] | None = (
            PythonManager.__execute_process([str(python_path), "--version"])
        )

        version = (
            result.stdout.lower().replace("python ", "").strip()
            if result is not None
            else "0.0.0"
        )
        return PythonVersion(version, python_path)

    @staticmethod
    def __get_current_version() -> PythonVersion:
        current_runtime = env_manager.get_python_runtime()
        current_version: PythonVersion = PythonVersion("0.0.0", Path())
        if current_runtime:
            current_version = PythonManager.__get_version(
                current_runtime
                if current_runtime.suffix == ".exe"
                else current_runtime / "python.exe"
            ) or PythonVersion("0.0.0", Path(""))
        return current_version

    @staticmethod
    def __read_python_directory_defaults() -> list[str]:
        found_directories: list[str] = []
        with open(DIRECTORY_DEFAULT_FILE) as file:
            data = json.load(file)
            found_directories = data["DirectoryDefaults"]

        return found_directories

    @staticmethod
    def __read_python_where(file_pattern: str) -> list[str]:
        WHERE_EXE: str = "where.exe"
        result: subprocess.CompletedProcess[str] | None = (
            PythonManager.__execute_process([WHERE_EXE, file_pattern])
        )
        if result:
            return result.stdout.strip().splitlines()
        else:
            return []

    @staticmethod
    def __execute_process(
        command: list[str],
    ) -> subprocess.CompletedProcess[str] | None:

        result: subprocess.CompletedProcess[str] | None = None
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
            with open("process_logs.txt", "a") as output:
                output.write(f"\nExecuting: {command}\n")
                output.write(f"ERROR: {result.stderr}\n")
                output.write(f"Std: {result.stdout}\n")
                output.write(f"Result: {result.returncode}\n")
                output.write(f"Args: {result.args}\n")
        except ValueError as e:
            logger.error(f"Error while running {command}: {e}")
        except FileNotFoundError as e:
            logger.error(f"File not found: {command}\n{e}")
        except (
            subprocess.TimeoutExpired,
            PermissionError,
        ) as e:
            logger.error(f"Error while running {command}\n {e}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Return Code: {e.returncode}")
            logger.error(f"Error: {e.stderr}")
            logger.error(f"where.exe command failed:\n{e}")
        except subprocess.SubprocessError as e:
            logger.error(f"Error while running python: {command}\n {e}")

        return result
