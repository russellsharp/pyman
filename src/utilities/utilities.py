import logging
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager, contextmanager
from enum import Enum
from pathlib import Path
from typing import IO, Any, Iterable, NamedTuple, cast

from common import setup_logger

logger = setup_logger(__name__, logging.INFO)


def get_file_contents(path: Path | None) -> str:
    if not path:
        raise ValueError("None path passed.")
    raw_text: str = ""
    with open(path, "r", encoding="utf-8") as raw_text_file:
        raw_text = raw_text_file.read()
    return raw_text


def get_value[T](key: str, default: T | None = None, **kwargs: Any) -> T:
    logger.debug(f"Looking for key: {key} in {kwargs}")
    if key in kwargs:
        logger.debug(f"Found key: {key} = {kwargs[key]}")
        return cast(T, kwargs[key])

    if default is not None:
        return default

    raise ValueError(f"Value for key, {key}, not found in kwargs.")


@contextmanager  # type: ignore
def safe_file(
    file: Path | str, mode: str = "a+", *, encoding: str = "utf-8", **kwargs: Any
) -> AbstractContextManager[IO[str]]:  # type: ignore
    f: IO[str] | None = None
    try:
        file_path: Path

        if isinstance(file, str):
            file_path: Path = Path(file)
        else:
            file_path = file

        file_path = file_path.resolve()

        if not (file_path.is_absolute() or file_path.name or file_path.suffix):
            raise ValueError(f"Path specified must include a file name: {file}")

        dir_path = file_path.parent

        dir_path.mkdir(parents=True, exist_ok=True)

        f = open(file_path, mode, encoding=encoding, **kwargs)

        yield f  # type: ignore

    finally:
        if f:
            f.close()


def find_new_file_path(parent_path: Path, file_name: str, file_ext: str) -> Path:
    index: int = 0
    INDEX_MAX: int = 99
    if not file_ext.startswith("."):
        file_ext = "." + file_ext
    while (
        new_file_path := parent_path / f"{file_name}_{index:02}{file_ext}"
    ) and new_file_path.exists():
        index += 1
        if index > INDEX_MAX:
            new_file_path = parent_path / f"{file_name}_{0:02}{file_ext}"
            break
    return new_file_path


type SupportedType = float | int | str | bool | Enum | None
type BoundPair = tuple[SupportedType, SupportedType]


class Bounds(NamedTuple):
    min: SupportedType
    max: SupportedType


def get_type_bounds(data_type: type[SupportedType]) -> Bounds:
    """Returns a tuple of (min_value, max_value) for a given type."""
    type_map: dict[type[SupportedType] | None, BoundPair] = {
        # Float: System hardware boundaries
        float: (-sys.float_info.max, sys.float_info.max),
        # Integer: Architecture-based limits (2^63)
        int: (-sys.maxsize - 1, sys.maxsize),
        # Boolean: False is 0 (min), True is 1 (max)
        bool: (False, True),
        # String: Empty string (min), No realistic max (conceptual limit used here)
        str: ("", chr(sys.maxunicode) * 100),
    }
    bounds: BoundPair = type_map.get(data_type, (None, None))

    if issubclass(data_type, Enum):
        bounds = get_enum_bounds(data_type)

    if bounds == (None, None):
        raise ValueError(f"Bounds requested for unsupported type or None: {data_type} ")

    return Bounds(min=bounds[0], max=bounds[1])


def get_enum_bounds(enum_class: type[Enum]) -> Bounds:
    values = [member.value for member in enum_class]
    return Bounds(min(values), max(values))


def last_index_of(values: list[Any], value: Any) -> int | None:
    return next((len(values) - 1 - i for i, x in enumerate(reversed(values)) if x == value), None)


def is_list_of_type(obj: Any, of_type: type) -> bool:
    return obj and isinstance(obj, list) and all(isinstance(item, of_type) for item in obj)  # type: ignore


def is_dict_of_type(obj: Any, of_type: type) -> bool:
    return obj and isinstance(obj, dict) and all(isinstance(item, of_type) for item in obj.values())  # type: ignore


def digits_in_str(subject: str) -> int:
    return sum(1 for c in subject if c.isdigit())


def print_depth(
    d: dict[str, Any] | Any,
    max_depth: int,
    current_depth: int = 1,
    func: Callable[[Any], None] = lambda msg: print(msg),
) -> None:
    if not isinstance(d, dict) or current_depth > max_depth:
        return

    for key, value in d.items():
        if isinstance(value, dict):
            func(f"{'\t' * current_depth}{key}:")
            print_depth(d=value, max_depth=max_depth, current_depth=current_depth + 1, func=func)
        else:
            func(f"{'\t' * current_depth}{key}: {value}")


def handle_collection(
    header: str,
    collection: Iterable[Any],
    func: Callable[[str], None],
    handle_item_func: Callable[..., Any] = lambda x: str(x),
    footer: str | None = None,
):
    func(header)
    for item in collection:
        if isinstance(item, tuple):
            func(handle_item_func(*item))
        else:
            func(handle_item_func(item))
    func(footer if footer is not None else header)
