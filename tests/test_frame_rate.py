from unittest import TestCase

import ffmpeg_tools as ffmpeg
from parameterized import parameterized


class TestFrameRate(TestCase):
    def test_should_have_a_default_for_divisor(self):
        self.assertEqual(ffmpeg.frame_rate.FrameRate(10), (10, 1))
        self.assertEqual(ffmpeg.frame_rate.FrameRate(10, 5), (10, 5))
        self.assertEqual(ffmpeg.frame_rate.FrameRate(10, 6), (10, 6))

    @parameterized.expand([
        (ffmpeg.frame_rate.FrameRate(30), (30, 1)),
        (ffmpeg.frame_rate.FrameRate('30'), ('30', 1)),
        (0, (0, 1)),
        (30, (30, 1)),
        (30.0, (30, 1)),
        ('30', (30, 1)),
        ('30/1', (30, 1)),
        ((30, 1), (30, 1)),
        ([30, 1], (30, 1)),
    ])
    def test_decode_should_parse_valid_representations(self, raw_value, expected_tuple):
        decoded_frame_rate = ffmpeg.frame_rate.FrameRate.decode(raw_value)
        self.assertIsInstance(decoded_frame_rate, ffmpeg.frame_rate.FrameRate)
        self.assertEqual(decoded_frame_rate, ffmpeg.frame_rate.FrameRate(*expected_tuple))

    @parameterized.expand([
        ('',),
        ('abc',),
        ('30.0'),
        ('30.1'),
        ('30/30/30',),
        (-30,),
        (30.1,),
        ((),),
        ([],),
        ((30, 1, 30),),
        ((30.1, 1),),
        ({},),
        (set(),),
    ])
    def test_decode_should_reject_invalid_representations(self, raw_value):
        with self.assertRaises(ValueError):
            ffmpeg.frame_rate.FrameRate.decode(raw_value)

    @parameterized.expand([
        (ffmpeg.frame_rate.FrameRate(30), (30, 1)),
        ((30, 1), (30, 1)),
        ([30, 1], (30, 1)),
        ((0,), (0, 1)),
        ((30,), (30, 1)),
        ((30, 1), (30, 1)),
        ((60, 2), (60, 2)),
        ((62, 4), (62, 4)),
    ])
    def test_from_collection_should_parse_valid_representations(self, collection, expected_tuple):
        parsed_frame_rate = ffmpeg.frame_rate.FrameRate.from_collection(collection)
        self.assertIsInstance(parsed_frame_rate, ffmpeg.frame_rate.FrameRate)
        self.assertEqual(parsed_frame_rate, ffmpeg.frame_rate.FrameRate(*expected_tuple))

    @parameterized.expand([
        ((),),
        ([],),
        ((30, 1, 30),),
        ([30, 1, 30],),
        ((30.0, 1),),
        ((30.1, 1),),
        ((30, '1'),),
        ((30, 1.5),),
        ((-1,),),
        ((10, -10),),
        ((-10, 10),),
        ((-10, -10),),
        ((10, 0),),
        (ffmpeg.frame_rate.FrameRate('30'),),
    ])
    def test_from_collection_should_reject_invalid_representations(self, collection):
        with self.assertRaises(ValueError):
            ffmpeg.frame_rate.FrameRate.from_collection(collection),

    @parameterized.expand([
        ('0', (0, 1)),
        ('30', (30, 1)),
        ('30/1', (30, 1)),
        ('60/2', (60, 2)),
        ('62/4', (62, 4)),
    ])
    def test_from_string_should_parse_valid_representations(self, string_value, expected_tuple):
        parsed_frame_rate = ffmpeg.frame_rate.FrameRate.from_string(string_value)
        self.assertIsInstance(parsed_frame_rate, ffmpeg.frame_rate.FrameRate)
        self.assertEqual(parsed_frame_rate, ffmpeg.frame_rate.FrameRate(*expected_tuple))

    @parameterized.expand([
        ('',),
        ('abc',),
        ('29.5',),
        ('30/1/2',),
        ('30/',),
        ('/1',),
        ('30/1.5',),
        ('-1',),
        ('10/-10',),
        ('-10/10',),
        ('-10/-10',),
    ])
    def test_from_string_should_reject_invalid_representations(self, string_value):
        with self.assertRaises(ValueError):
            ffmpeg.frame_rate.FrameRate.from_string(string_value),

    @parameterized.expand([
        ((0, 1), (0, 1)),
        ((30, 1), (30, 1)),
        ((5, 13), (5, 13)),
        ((60, 2), (30, 1)),
        ((62, 4), (31, 2)),
    ])
    def test_normalized_should_return_values_without_common_divisors(self, input_tuple, expected_tuple):
        normalized_frame_rate = ffmpeg.frame_rate.FrameRate(*input_tuple).normalized()
        self.assertIsInstance(normalized_frame_rate, ffmpeg.frame_rate.FrameRate)
        self.assertEqual(normalized_frame_rate, ffmpeg.frame_rate.FrameRate(*expected_tuple))

    def test_to_float(self):
        self.assertEqual(ffmpeg.frame_rate.FrameRate(10).to_float(), 10.0)
        self.assertEqual(ffmpeg.frame_rate.FrameRate(5, 2).to_float(), 2.5)
        self.assertEqual(ffmpeg.frame_rate.FrameRate(10, 2).to_float(), 5.0)

    def test_should_have_unambiguous_string_representation(self):
        self.assertEqual(str(ffmpeg.frame_rate.FrameRate(10)), "10/1")
        self.assertEqual(str(ffmpeg.frame_rate.FrameRate(10, 5)), "10/5")
        self.assertEqual(str(ffmpeg.frame_rate.FrameRate(10, 6)), "10/6")

