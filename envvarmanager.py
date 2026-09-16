import ctypes
import logging
import os
import winreg
from abc import ABC, abstractmethod
from ctypes import wintypes
from enum import Enum
from pathlib import Path

from elevate import elevate  # type: ignore

ENV_VAR_PYTHON_KEY = "PYTHON_ACTIVE_RUNTIME"
ENV_VAR_PATH = "PATH"
ENV_VAR_REG_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.propagate = True


class IEnvManager(ABC):
    @abstractmethod
    def set_python_runtime(self, runtime_directory: Path) -> None:
        pass

    @abstractmethod
    def get_python_runtime(self, key: str = ENV_VAR_PYTHON_KEY) -> Path | None:
        pass

    @abstractmethod
    def set(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def get(selfg, key: str) -> str | None:
        pass

    @abstractmethod
    def check_privilege(self) -> None:
        pass


# TODO Make cross-platform
class Context(Enum):
    USER = winreg.HKEY_CURRENT_USER
    SYSTEM = winreg.HKEY_LOCAL_MACHINE


class WindowsEnvManager(IEnvManager):
    def set_python_runtime(self, runtime_directory: Path) -> None:
        if runtime_directory.suffix == ".exe":
            runtime_directory = runtime_directory.parent
        self.set(ENV_VAR_PYTHON_KEY, str(runtime_directory))

    def get_python_runtime(self, key: str = ENV_VAR_PYTHON_KEY) -> Path | None:
        path = self.get(key)
        return Path(path) if path else None

    def check_path_for_python_var(self, key: str) -> bool:
        path: str | None = self.get(ENV_VAR_PATH)
        return path is not None and key in path

    def get(self, key: str) -> str | None:
        # check_privilege()
        return os.getenv(key)

    def set(self, key: str, value: str) -> None:
        self.check_privilege()
        os.environ[key] = value
        self.set_windows_env_var(key, value)

    def check_privilege(self) -> None:
        elevate()

    def set_windows_env_var(
        self, name: str, value: str, context: Context = Context.SYSTEM
    ):
        self.check_privilege()
        # Path to the Windows System environment variables in the registry
        reg_path = ENV_VAR_REG_KEY

        try:
            # Open the registry key with write permissions
            key = winreg.OpenKey(int(context.value), reg_path, 0, winreg.KEY_SET_VALUE)

            # Set the value (REG_EXPAND_SZ allows using variables like %SystemRoot%)
            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
            winreg.CloseKey(key)
            # Set a persistent environment variable for the context
            try:
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002

                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST,
                    WM_SETTINGCHANGE,
                    0,
                    "Environment",
                    SMTO_ABORTIFHUNG,
                    5000,  # 5 second timeout
                    ctypes.byref(wintypes.DWORD()),
                )
            except Exception as e:
                logger.info(e)
            print(f"Successfully set {name} system-wide.")

        except PermissionError:
            print("Error: You must run this script as an Administrator!")
