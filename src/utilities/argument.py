from enum import Enum, IntEnum, StrEnum

import pytest

from common import setup_logger
from src.utilities.utilities import Bounds, get_enum_bounds, get_type_bounds

logger = setup_logger(__name__)

ArgumentType = float | int | bool | str | Enum


class Argument[ArgumentType]:
    def __init__(self, name: str, min: ArgumentType, max: ArgumentType, default: ArgumentType):
        self.name: str = name
        self.min: ArgumentType = min
        self.max: ArgumentType = max
        self.default: ArgumentType = default
        self._value = default
        self.type: type = type(default)

    @property
    def value(self) -> ArgumentType:
        return self._value

    @value.setter
    def value(self, val: ArgumentType) -> None:
        if val < self.min or val > self.max:
            raise ValueError(
                f"Value provided for {self.name}, {val}, is outside of range: [{self.min} - {self.max}]"
            )
        self._value = val


class ArgumentCollection:
    _collection_name: str = "_collection"

    def __init__(self, arguments: dict[str, Argument[ArgumentType]]):
        self._collection: dict[str, Argument[ArgumentType]]
        super().__setattr__(ArgumentCollection._collection_name, arguments)

    def __setattr__(self, name: str, value: ArgumentType):

        if name in self._collection:
            self._collection[name].value = value
        else:
            val_type = type(value)
            bounds: Bounds = get_type_bounds(val_type)
            self._collection[name] = Argument(
                name, val_type(bounds.min), val_type(bounds.max), value
            )

    def __getattr__(self, name: str) -> ArgumentType | None:
        if name in self._collection:
            return self._collection[name].value

    def __setitem__(self, name: str, value: ArgumentType) -> None:
        if name in self._collection:
            self._collection[name].value = value
        else:
            val_type = type(value)
            bounds: Bounds = get_type_bounds(val_type)
            self._collection[name] = Argument(
                name, val_type(bounds.min), val_type(bounds.max), value
            )

    def __getitem__(self, name: str) -> ArgumentType | None:
        if name in self._collection:
            return self._collection[name].value

    @property
    def parameters(self) -> dict[str, ArgumentType]:
        return {key: item.value for key, item in self._collection.items()}


def test_new_param() -> None:
    coll: ArgumentCollection = ArgumentCollection(
        {"width_ths": Argument("width_ths", 0.2, 2.0, 0.4)}
    )
    assert coll

    coll.new_param = "hello"

    assert coll.new_param == "hello"

    coll.new_param_int = 5

    assert coll.new_param_int == 5


def test_use_collection() -> None:
    coll: ArgumentCollection = ArgumentCollection(
        {"width_ths": Argument("width_ths", 0.2, 2.0, 0.4)}
    )
    assert coll
    coll.width_ths = 0.2

    assert coll.width_ths == 0.2

    with pytest.raises(ValueError):
        coll.width_ths = 5.0

    with pytest.raises(ValueError):
        coll.width_ths = 0.0


def test_get_parameters() -> None:
    defaults: dict[str, Argument[ArgumentType]] = {
        "paragraph": Argument("paragraph", False, True, False),
        "x_threshold": Argument("x_threshold", 0.1, 1, 1),
        "y_threshold": Argument("y_threshold", 0.1, 1, 0.5),
        "width_ths": Argument("width_ths", 0.1, 1, 0.5),
        "height_ths": Argument("height_ths", 0.1, 1, 0.5),
        "slope_ths": Argument("slope_ths", 0.1, 1, 0.1),
        # used when paragraph = True
        "add_margin": Argument("add_margin", 0.1, 1, 0.1),
        "link_threshold": Argument("link_threshold", 0.1, 1, 0.4),
        "low_text": Argument("low_text", 0.1, 1, 0.4),
        "canvas_size": Argument("canvas_size", 0.1, 1, 2560),
        "mag_ratio": Argument("mag_ratio", 0.1, 1, 1.0),
    }
    reader_args: ArgumentCollection = ArgumentCollection(defaults)
    reader_args.paragraph = True

    assert reader_args
    assert reader_args.paragraph == True
    assert reader_args.width_ths == 0.5

    effective_parameters = reader_args.parameters
    assert effective_parameters["width_ths"] == 0.5
    assert len(effective_parameters) == 11

    reader_args.new_param = "Hello"
    effective_parameters = reader_args.parameters
    assert effective_parameters["width_ths"] == 0.5
    assert len(effective_parameters) == 12


def test_enum_bounds() -> None:

    class TestEnum(StrEnum):
        FIRST = "1"
        TWO = "2"
        LAST = "3"

    enum_bounds = get_enum_bounds(TestEnum)

    assert enum_bounds == (TestEnum.FIRST, TestEnum.LAST)

    instance_enum: TestEnum = TestEnum.FIRST

    enum_type_bounds = get_enum_bounds(type(instance_enum))

    assert enum_type_bounds == (TestEnum.FIRST, TestEnum.LAST)

    enum_generic_bounds = get_type_bounds(TestEnum)

    assert enum_generic_bounds == (TestEnum.FIRST, TestEnum.LAST)


def test_enum_int_bounds():
    class TestEnum(IntEnum):
        FIRST = 1
        SECOND = 2
        LAST = 3

    enum_bounds = get_enum_bounds(TestEnum)

    assert enum_bounds == (TestEnum.FIRST, TestEnum.LAST)

    instance_enum: TestEnum = TestEnum.FIRST

    enum_type_bounds = get_enum_bounds(type(instance_enum))

    assert enum_type_bounds == (TestEnum.FIRST, TestEnum.LAST)

    enum_generic_bounds = get_type_bounds(TestEnum)

    assert enum_generic_bounds == (TestEnum.FIRST, TestEnum.LAST)
