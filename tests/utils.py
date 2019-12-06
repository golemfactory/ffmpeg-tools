import os
from typing import List

from ffmpeg_tools import commands


def get_absolute_resource_path(filename: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resources',
        filename
    )


def make_parameterized_test_name_generator_for_scalar_values(scalar_names: List[str]):
    def test_case_name_generator(testcase_func, param_num, param):
        assert len(param[0]) == len(scalar_names)

        scalar_values = [str(value) for value in param[0]]
        parameter_names_and_values = '_'.join(commands.flatten_list(zip(scalar_names, scalar_values)))

        return f'{testcase_func.__name__}_{param_num}_{parameter_names_and_values}'

    return test_case_name_generator
