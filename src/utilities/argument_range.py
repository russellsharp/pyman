from collections.abc import Iterator
from enum import Enum
import logging
import sys
from typing import Any, SupportsIndex

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler(sys.stdout)
logger.addHandler(console_handler)
logger.setLevel(logging.INFO)


class BaseRange:
    def __init__(self, start: Any, stop: Any, step: Any):
        self._start = start
        self._stop = stop
        self._step = step

    def __iter__(self):
        return self.range()

    def range(self) -> Iterator[Any]:
        raise NotImplementedError()


class RangeBool(BaseRange):
    def __init__(self):
        self._start = False
        self._stop = True
        self._step = 1
        self._values = [False, True]

    def range(self) -> Iterator[bool]:
        yield from self._values


class RangeEnum(BaseRange):
    def __init__(self, enumeration: type[Enum], step: int = 1):
        self._values = list(enumeration)
        if len(self._values) <= 0:
            raise ValueError("Empty enumeration given.")
        self._start = self._values[0]
        self._stop = self._values[-1]
        self._step: int = step

    def range(self) -> Iterator[Enum]:
        if self._step > 0:
            yield from self._values
        else:
            yield from reversed(self._values)


class RangeList(BaseRange):
    def __init__(self, start: Any, stop: Any, values: list[Any], step: int = 1):
        self._values = values
        super().__init__(start, stop, step)

    def range(self) -> Iterator[Any]:
        current_index: SupportsIndex = self._values.index(self._start)

        indices_of_start: list[int] = [
            int(i) for i, v in enumerate(self._values) if v == self._start
        ]
        indices_of_stop: list[int] = [int(i) for i, v in enumerate(self._values) if v == self._stop]

        if self._step > 0:
            start_index: SupportsIndex = min(indices_of_start, default=0)
            stop_index: SupportsIndex = max(
                [i for i in indices_of_stop if i >= start_index],
                default=(max(len(self._values) - 1, 0)),
            )
            current_index = start_index
            while start_index <= current_index and (
                start_index == stop_index == current_index or current_index < stop_index
            ):
                yield self._values[current_index]
                current_index += int(self._step)
        else:
            start_index: SupportsIndex = max(
                indices_of_start, default=max(len(self._values) - 1, 0)
            )
            stop_index: SupportsIndex = min(min(indices_of_stop, default=0), start_index)
            current_index = start_index

            while (
                start_index == stop_index == current_index or current_index > stop_index
            ) and current_index <= start_index:
                yield self._values[current_index]
                current_index += int(self._step)


class RangeInt(BaseRange):
    def __init__(self, start: int, stop: int, step: int = 1):
        super().__init__(start, stop, step)

    def range(self) -> Iterator[int]:
        current: int = self._start
        if self._step > 0:
            while current < self._stop:
                yield current
                current += self._step
        else:
            while current > self._stop:
                yield current
                current += self._step


class RangeFloat(BaseRange):
    def __init__(self, start: float, stop: float, step: float = 0.1, decimal_precision: int = 3):
        super().__init__(start, stop, step)
        self._decimal_precision: int = decimal_precision

    def range(self) -> Iterator[float]:
        current: float = self._start
        if self._step > 0:
            while current < self._stop:
                yield round(current, self._decimal_precision)
                current += round(self._step, self._decimal_precision)
        else:
            while current > self._stop:
                yield round(current, self._decimal_precision)
                current += round(self._step, self._decimal_precision)


def test_range_float():
    range = RangeFloat(0, 25.5, 0.5)
    values = [val for val in range.range()]
    assert values
    assert len(values) > 49
    values[0] = 0
    values[49] = 25

    range = RangeFloat(0, 26.6, 0.1, 3)
    values = [val for val in range.range()]
    assert values
    assert len(values) == 266
    assert values[0] == 0
    assert values[265] == 26.5

    range = RangeBool()
    values = [val for val in range.range()]
    assert values == [False, True]

    range = RangeList("four", "one", ["one", "two", "three", "four"])
    values = [val for val in range.range()]
    assert values == ["four"]

    range = RangeList("one", "four", ["one", "two", "three", "four"])
    values = [val for val in range.range()]
    assert values == [
        "one",
        "two",
        "three",
    ]

    range = RangeList("one", "four", ["one", "two", "three", "four", "five"], 2)
    values = [val for val in range.range()]
    assert values == ["one", "three"]

    range = RangeList("five", "one", ["one", "two", "three", "four", "five"], -1)
    values = [val for val in range.range()]
    assert values == ["five", "four", "three", "two"]

    range = RangeList("five", "one", ["one", "two", "three", "four", "five"], 2)
    values = [val for val in range.range()]
    assert values == ["five"]

    range = RangeList("one", "five", ["one", "two", "three", "four", "five"], 2)
    values = [val for val in range.range()]
    assert values == ["one", "three"]

    range = RangeList("one", "five", ["one", "two", "three", "four", "five", "six"], 2)
    values = [val for val in range.range()]
    assert values == ["one", "three"]

    range = RangeList("one", "five", ["one", "two", "three", "four", "five", "six"], -2)
    values = [val for val in range.range()]
    assert values == ["one"]

    range = RangeList("five", "one", ["one", "two", "three", "four", "five", "six"], -2)
    values = [val for val in range.range()]
    assert values == ["five", "three"]

    class MyEnum(Enum):
        FirstValue = 0
        SecondValue = 4
        ThirdValue = "Bird"
        LastValue = "I'llSwallowYourSoooooul"

    range = RangeEnum(MyEnum)
    values = [val for val in range.range()]
    assert values == [MyEnum.FirstValue, MyEnum.SecondValue, MyEnum.ThirdValue, MyEnum.LastValue]

    range = RangeEnum(MyEnum, -1)
    values = [val for val in range.range()]
    assert values == [MyEnum.LastValue, MyEnum.ThirdValue, MyEnum.SecondValue, MyEnum.FirstValue]
