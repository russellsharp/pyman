import typer

from common import setup_logger
from src.envvarmanager import IEnvManager, WindowsEnvManager
from src.pythonmanager import PythonManager

app: typer.Typer = typer.Typer(
    chain=True,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
)

logger = setup_logger(__name__)

app.command(name="pick")(PythonManager.choose_version)
app.command(name="list")(PythonManager.list_versions)

env_manager: IEnvManager = WindowsEnvManager()

if __name__ == "__main__":
    env_manager.check_privilege()
    app()
