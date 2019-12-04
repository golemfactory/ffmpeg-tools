from math import gcd
from typing import Any, NamedTuple, Union


class FrameRate(NamedTuple):
    dividend: int
    divisor: int = 1

    @classmethod
    def decode(cls, raw_value: Any) -> 'FrameRate':
        if isinstance(raw_value, str):
            return cls.from_string(raw_value)
        if isinstance(raw_value, int):
            return cls.from_collection((raw_value,))
        if isinstance(raw_value, float):
            int_value = int(raw_value)
            if raw_value == int_value:
                return cls.from_collection((int_value,))

            raise ValueError(
                "Expressing frame rate using a floating point number is not supported. "
                "To get accurate results you should always specify it as a ratio of two integers."
            )
        if isinstance(raw_value, FrameRate):
            return raw_value
        if isinstance(raw_value, (list, tuple)):
            return cls.from_collection(raw_value)

        raise ValueError(f"Value of type {type(raw_value)} could not be interpreted as frame rate")

    @classmethod
    def from_collection(cls, collection: Union[list, tuple]) -> 'FrameRate':
        if len(collection) not in [1, 2] or not all(isinstance(i, int) for i in collection):
            raise ValueError(f"Only (int, int), or (int,) can be interpreted as a frame rate")

        if len(collection) == 1:
            (dividend, divisor) = (collection[0], 1)
        else:
            (dividend, divisor) = (collection[0], collection[1])

        if dividend < 0 or divisor < 0:
            raise ValueError("Frame rate can't be negative")

        if divisor == 0:
            raise ValueError("Divisor of the frame rate can't be zero")

        return cls(dividend, divisor)

    @classmethod
    def from_string(cls, string_value: str) -> 'FrameRate':
        return cls.from_collection([int(i) for i in string_value.split('/', 1)])

    def normalized(self) -> 'FrameRate':
        assert self.dividend >= 0
        assert self.divisor > 0

        common_divisor = gcd(self.dividend, self.divisor)
        return FrameRate(
            self.dividend // common_divisor,
            self.divisor // common_divisor,
        )

    def to_float(self) -> float:
        return self.dividend / self.divisor

    def __str__(self):
        # ASSUMPTION: this representation is unambiguous and directly usable
        # as a command-line argument for ffmpeg
        return f"{self.dividend}/{self.divisor}"
