# Pyman

## AI

Only README.MD is written by AI.

## Overview

Pyman is a Windows-focused Python runtime manager. It discovers installed Python versions, lists them, and lets the user switch the active runtime by updating the `PYTHON_ACTIVE_RUNTIME` environment variable and the Windows system environment configuration.

This project is intended for managing multiple Python installations on a Windows machine and making it easier to choose which version should be used in the current shell environment.

## Project layout

- `pyman.py`  
  Main CLI entry point. Registers the Typer commands for listing and selecting Python runtimes.
- `pythonmanager.py`  
  Core logic for discovering Python installations, checking the current runtime, and prompting the user to choose a version.
- `pythonversion.py`  
  Small value object used to store a Python version and its executable path.
- `envvarmanager.py`  
  Windows environment management logic for reading and writing the active Python runtime information.
- `default_directories.json`  
  Default search directories used when scanning for installed Python runtimes.
- `pyproject.toml`  
  Project metadata and Python/dependency configuration.

## Requirements

- Python 3.14 (as declared in `pyproject.toml`)
- Windows environment support
- Administrator privileges may be required when writing the system-level environment variable

## Dependencies

The project uses the following Python packages:

- pytest
- argparse
- flask
- typer
- elevate
- pyinstaller

## Usage

From the project root, run:

```bash
python pyman.py --help
```

List installed Python runtimes:

```bash
python pyman.py list
```

Choose the active Python runtime:

```bash
python pyman.py pick
```

The app searches default directories, common Python install locations, and results from the Windows `where.exe` lookup for `python.exe` candidates. It then prompts the user to select a version to use.

## Behavior

- Discovers Python installations in configured folders and PATH.
- Shows the current active runtime with an asterisk when listed.
- Lets the user select another runtime and stores the update in the environment.
- Prompts the user to run `refreshenv` in the terminal to refresh the active Python runtime for the current shell session.

## Notes

- This utility is designed primarily for Windows and uses registry/environment manipulation.
- The environment variable used is `PYTHON_ACTIVE_RUNTIME`.
- The script can require elevated permissions to set system-wide environment values.

## Development

This workspace is a simple Python utility project and does not currently include a full test suite or packaging workflow beyond the metadata in `pyproject.toml`.

## License

No explicit license file is included in this workspace.
