import logging

import typer

from envvarmanager import IEnvManager, WindowsEnvManager
from pythonmanager import PythonManager

app: typer.Typer = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)

logger = logging.getLogger()
stream_handler = logging.StreamHandler()
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

app.command(name="pick")(PythonManager.choose_version)
app.command(name="list")(PythonManager.list_versions)

env_manager: IEnvManager = WindowsEnvManager()

if __name__ == "__main__":
    env_manager.check_privilege()
    app()
