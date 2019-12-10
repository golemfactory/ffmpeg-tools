from typing import Optional, Set, Tuple, Union


Subrange = Union[int, Tuple[Optional[int], Optional[int]]]


class SparseRange:
    def __init__(self, subranges: Set[Subrange]):
        assert all(
            isinstance(subrange, int)
            or subrange[0] is None
            or subrange[1] is None
            or subrange[0] <= subrange[1]
            for subrange in subranges
        )

        self._points = {subrange for subrange in subranges if not isinstance(subrange, tuple)}
        self._ranges = {subrange for subrange in subranges if isinstance(subrange, tuple)}

    def contains(self, value: int) -> bool:
        if value in self._points:
            return True

        for range in self._ranges:
            if range[0] == range[1] == None:
                return True

            finite_range = (
                range[0] if range[0] is not None else min(value, range[1]),
                range[1] if range[1] is not None else max(value, range[0]),
            )
            assert finite_range[0] <= finite_range[1]

            if finite_range[0] <= value <= finite_range[1]:
                return True

        return False
