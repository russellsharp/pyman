import time
from enum import Enum
from typing import Any


class Measure:
    def __init__(self):
        self._times: dict[Enum, MeasuredTime] = {}

    def start(self, category: Enum):
        self._times[category] = MeasuredTime(start=time.perf_counter())

    def stop(self, category: Enum):
        if category not in self._times:
            raise ValueError(f"Stop timing for OCR without having started. Category: {category}")
        self._times[category].stop = time.perf_counter()

    def get_timings(self) -> dict[Enum, float]:
        timings: dict[Enum, float] = {}
        for category, timing in self._times.items():
            timings.update({category: timing.duration})
        return timings


class MeasuredTime:
    def __init__(self, start: float):
        self.start: float = start
        self.stop: float

    @property
    def duration(self) -> float:
        return self.stop - self.start

    def __repr__(self) -> str:
        return str(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return {"start": self.start, "stop": self.stop, "duration": self.duration}
