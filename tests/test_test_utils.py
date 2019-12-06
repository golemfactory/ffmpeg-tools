from unittest import TestCase

from tests.utils import make_parameterized_test_name_generator_for_scalar_values


def dummy_function(*_args, **_kwargs):
    pass


class TestTestUtilsMakeParameterizedTestNameGenerator(TestCase):
    def test_should_return_a_function_that_generates_names(self):
        generator = make_parameterized_test_name_generator_for_scalar_values(['a', 'b', 'c'])
        self.assertTrue(callable(generator))

        name = generator(dummy_function, 777, [['x', 'y', 'z']])
        self.assertEqual(name, "dummy_function_777_a_x_b_y_c_z")

    def test_should_handle_basic_scalar_types(self):
        generator = make_parameterized_test_name_generator_for_scalar_values(['a', 'b', 'c', 'd', 'e', 'f'])
        name = generator(dummy_function, 777, [[
            3,
            5.0,
            'stuff',
            False,
            True,
            None,
        ]])

        self.assertEqual(name, "dummy_function_777_a_3_b_5.0_c_stuff_d_False_e_True_f_None")

    def test_should_not_fail_if_it_gets_a_collection_or_object(self):
        generator = make_parameterized_test_name_generator_for_scalar_values(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'])
        name = generator(dummy_function, 777, [[
            [],
            [1, 2, 3],
            (1, 2, 3),
            {'a': 1},
            {1, 2, 3},
            [[], (), {}, set()],
            [[1, 2], ([([{4: 5}],)],), {}, set()],
            object(),
        ]])

        # It should not fail but the name does not have to be sensibly formatted.
        # We don't want to rely here on its exact structure.
        self.assertTrue(name.startswith("dummy_function_777_"))
