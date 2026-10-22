import os
import subprocess
from pathlib import Path
from typing import Annotated

import click
import typer

from common import setup_logger
from config import CONFIG_PATH
from src.configuration import Configuration
from src.envvarmanager import IEnvManager, WindowsEnvManager
from src.pythonversion import PythonVersion
from src.utilities.utilities import handle_collection

logger = setup_logger(__name__)


class DirectoryDoesNotExist(BaseException):
    def __init__(self, directory: str = "Unknown directory"):
        super().__init__(f"Directory not found: {directory}")


env_manager: IEnvManager = WindowsEnvManager()

configuration = Configuration.load_json(CONFIG_PATH)


class PythonManager:
    @staticmethod
    def list_versions(
        directories: Annotated[
            list[str] | None, typer.Argument(help="Directories to check for python.")
        ] = None,
        file_pattern: Annotated[
            str, typer.Option(help="File name of python executable")
        ] = "python.exe",
        max_depth: Annotated[
            int | None, typer.Option(help="Maximum depth to traverse from given directories.")
        ] = None,
    ) -> None:
        logger.info("Scanning for python executables.")
        if max_depth is None:
            max_depth = configuration.max_depth

        handle_collection("Default directories", configuration.default_directories, logger.debug)
        directories = directories or []
        directories.extend([str(path) for path in configuration.default_directories])
        directories.extend(PythonManager.__read_python_where(file_pattern))

        versions: set[PythonVersion] = set(
            PythonManager.__find_versions(directories, file_pattern, max_depth)
        )
        current_version = PythonManager.__get_current_version()
        versions.add(current_version)

        if len(versions) <= 0:
            typer.echo("No python installation found.")
            return
        # unique set of versions to display
        unique_ordered_versions = list(dict.fromkeys(versions))
        for v in unique_ordered_versions:
            typer.echo(str(v) + " *" if v == current_version else v)
        input("Press any key.")

    @staticmethod
    def choose_version(
        directories: Annotated[
            list[str] | None, typer.Argument(help="Directories to check for python.")
        ] = None,
        file_pattern: Annotated[
            str, typer.Option(help="File name of python executable")
        ] = "python.exe",
        max_depth: Annotated[
            int | None, typer.Option(help="Maximum depth to traverse from given directories.")
        ] = None,
    ) -> None:
        if max_depth is None:
            max_depth = configuration.max_depth

        directories = directories or []
        directories.extend([str(path) for path in configuration.default_directories])
        directories.extend(PythonManager.__read_python_where(file_pattern))

        pythons = PythonManager.__find_versions(directories, file_pattern, max_depth=max_depth)

        if len(pythons) <= 0:
            typer.echo(
                "python versions not found in given directories, default directories, or where.exe call."
            )
            return

        pythons_ordered_unique = list(dict.fromkeys(pythons))

        version_choice: PythonVersion | None = PythonManager.__prompt_versions(
            pythons_ordered_unique
        )

        if version_choice:
            env_manager.set_python_runtime(version_choice.Path)
            typer.echo(f"Set active python runtime to {version_choice}")
            typer.echo("Run 'refreshenv' to refresh the active python runtime for this terminal.")
        else:
            typer.echo("Python runtime version unchanged.")
        click.pause(info=f"Active python runtime version is {env_manager.get_python_runtime()}")

    @staticmethod
    def __find_versions(
        directories: list[str], file_pattern: str = "python.exe", max_depth: int = 3
    ) -> list[PythonVersion]:

        paths: list[Path] = [PythonManager.__resolve_directory(f) for f in directories]
        pythons: list[Path] = []

        for path in paths:
            pythons.extend(
                PythonManager.__find_file_recurse(path, file_pattern, max_depth=max_depth)
            )
        versions: list[PythonVersion] = [PythonManager.__get_version(py) for py in pythons]
        return versions

    @staticmethod
    def __prompt_versions(versions: list[PythonVersion]) -> PythonVersion | None:
        current_version = PythonManager.__get_current_version()
        selected = None
        prompt = ""

        unique_ordered_versions = list(dict.fromkeys(versions))
        for i, v in enumerate(unique_ordered_versions):
            prompt += f"\n({i}) {v.Path} - {v.Version}"
            if v == current_version:
                selected = i
                prompt += " *"
        prompt += "\nSelect Version. Default"

        choice: int = 0
        while True:
            choice = typer.prompt(prompt, type=int, default=selected)
            if choice >= 0 and choice < len(unique_ordered_versions):
                break

            typer.secho(
                f"Error: Choice must be between 0 and {len(unique_ordered_versions) - 1}.",
                fg=typer.colors.RED,
            )

        return (
            unique_ordered_versions[choice]
            if unique_ordered_versions[choice] != current_version
            else None
        )

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
        directory: Path, file_pattern: str = "python.exe", max_depth: int = 3
    ) -> list[Path]:
        paths: list[Path] = []

        if not directory.exists():
            logger.error(f"DIRECTORY DOES NOT EXIST: {directory}")
            return []

        if directory.is_file() and directory.match(file_pattern):
            paths.append(Path(directory))

        base_depth: int = len(directory.parts)

        for root, subdirs, files in directory.walk(top_down=True):
            current_depth = len(root.parts) - base_depth

            if current_depth >= max_depth:
                subdirs.clear()
            # prepending root directory is necessary
            file_paths = [Path(root / f) for f in files]

            paths.extend(f for f in file_paths if f.is_file() and f.match(file_pattern))
        return paths

    @staticmethod
    def ___walk_with_max_depth(root_path: Path, max_depth: int = 3):
        base_depth = len(root_path.parts)

        for root, subdirs, files in root_path.walk():
            yield root, subdirs, files

            current_depth = len(root.parts) - base_depth

            if current_depth >= max_depth:
                subdirs.clear()

    @staticmethod
    def __get_version(python_path: Path | str) -> PythonVersion:
        env_manager.check_privilege()
        python_path = Path(python_path) if isinstance(python_path, str) else python_path
        python_path = python_path / "python.exe" if python_path.is_dir() else python_path

        result: subprocess.CompletedProcess[str] | None = PythonManager.__execute_process(
            [str(python_path), "--version"]
        )

        version = (
            result.stdout.lower().replace("python ", "").strip() if result is not None else "0.0.0"
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
    def __read_python_where(file_pattern: str) -> list[str]:
        WHERE_EXE: str = "where.exe"
        result: subprocess.CompletedProcess[str] | None = PythonManager.__execute_process(
            [WHERE_EXE, file_pattern]
        )
        if result:
            return result.stdout.replace("\\\\", "\\").splitlines()
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
