from unittest import TestCase
from parameterized import parameterized

from ffmpeg_tools import utils
from tests.utils import make_parameterized_test_name_generator_for_scalar_values


class TestSparseRange(TestCase):
    @parameterized.expand(
        [
            (set(), 0, False),
            ({1, 2, 3}, 1, True),
            ({1, 2, 3}, 3, True),
            ({1, 2, 3}, 5, False),
            ({-5, 0, 5}, -5, True),
            ({-5, 0, 5}, -4, False),
            ({(1, 5)}, 0, False),
            ({(1, 5)}, 1, True),
            ({(1, 5)}, 3, True),
            ({(1, 5)}, 5, True),
            ({(1, 5)}, 6, False),
            ({(1, 5), (10, 15)}, 3, True),
            ({(1, 5), (10, 15)}, 7, False),
            ({(1, 5), (10, 15)}, 12, True),
            ({1, (10, 15)}, 1, True),
            ({1, (10, 15)}, 3, False),
            ({1, (10, 15)}, 12, True),
            ({(10, None)}, 12, True),
            ({(10, None)}, 12000, True),
            ({(10, None)}, 9, False),
            ({(None, 10)}, 11, False),
            ({(None, 10)}, 9, True),
            ({(None, 10)}, -12000, True),
            ({(None, None)}, -12000, True),
            ({(None, None)}, 0, True),
            ({(None, None)}, 12000, True),
            ({(10, None), 12}, 10, True),
            ({(10, None), 12}, 11, True),
            ({(10, None), 12}, 12, True),
            ({1, 2, 3, (1, 3)}, 0, False),
            ({1, 2, 3, (1, 3)}, 1, True),
            ({1, 2, 3, (1, 3)}, 2, True),
            ({1, 2, 3, (1, 3)}, 3, True),
            ({1, 2, 3, (1, 3)}, 4, False),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['subrange', 'value', 'result']),
    )
    def test_contains(self, subranges, value, expected_result):
        self.assertEqual(utils.SparseRange(subranges).contains(value), expected_result)

