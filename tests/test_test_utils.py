import os
import tempfile
import shutil
from unittest import TestCase

from ffmpeg_tools import commands
from ffmpeg_tools import meta
from tests.utils import generate_sample_video, generate_sample_video_command, \
    get_absolute_resource_path, SAMPLE_STREAM_SOURCES, make_parameterized_test_name_generator_for_scalar_values


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


class TestTestUtilsBuildTestVideo(TestCase):
    # This is meant to include all the available codecs and should be kept up to
    # date as we add or remove supported codecs. Unfortunately no container
    # supports 100% of them (even matroska does not support some subtitle codecs)
    # so sometimes you may have to subtract a codec from the set in the assert
    # below.
    ALMOST_ALL_STREAMS = [
        ('video', 'h264'),
        ('video', 'mjpeg'),
        ('video', 'flv1'),
        ('audio', 'aac'),
        ('audio', 'mp3'),
        ('subtitle', 'subrip'),
        ('subtitle', 'ass'),
        ('subtitle', 'webvtt'),
    ]
    assert set(n for t, n in ALMOST_ALL_STREAMS) == (set(SAMPLE_STREAM_SOURCES) - {'mov_text'}), \
        "If you add something to SAMPLE_STREAM_SOURCES, you should add it above too"

    def setUp(self):
        # I want to see full diff in test output. It's not all that long.
        self.maxDiff = 10000

        self.tmp_dir = os.path.join(tempfile.mkdtemp(prefix='ffmpeg-tools-test-utils-test-'))

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_generate_sample_video_command(self):
        output_path = os.path.join(self.tmp_dir, 'output.mkv')
        requested_streams = [codec_name for codec_type, codec_name in self.ALMOST_ALL_STREAMS]

        expected_command = [
            commands.FFMPEG_COMMAND,
            "-nostdin",
            "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
            "-i", get_absolute_resource_path('sample.srt'),
            "-map", "0:0",
            "-codec:0", "h264",
            "-map", "0:0",
            "-codec:1", "mjpeg",
            "-map", "0:0",
            "-codec:2", "flv1",
            "-map", "0:1",
            "-codec:3", "aac",
            "-map", "0:1",
            "-codec:4", "mp3",
            "-map", "1:0",
            "-codec:5", "subrip",
            "-map", "1:0",
            "-codec:6", "ass",
            "-map", "1:0",
            "-codec:7", "webvtt",
            "-f", "matroska",
            output_path,
        ]

        command = generate_sample_video_command(
            requested_streams,
            output_path,
            container='matroska',
        )

        self.assertEqual(command, expected_command)

    def test_generate_sample_video_command_should_support_multiple_streams_with_same_codec(self):
        output_path = os.path.join(self.tmp_dir, 'output.mp4')
        requested_streams_with_types = [
            ('subtitle', 'mov_text'),
            ('video', 'h264'),
            ('video', 'h264'),
            ('subtitle', 'mov_text'),
        ]
        requested_streams = [codec_name for codec_type, codec_name in requested_streams_with_types]

        expected_command = [
            commands.FFMPEG_COMMAND,
            "-nostdin",
            "-i", get_absolute_resource_path('sample.srt'),
            "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
            "-map", "0:0",
            "-codec:0", "mov_text",
            "-map", "1:0",
            "-codec:1", "h264",
            "-map", "1:0",
            "-codec:2", "h264",
            "-map", "0:0",
            "-codec:3", "mov_text",
            "-f", "mp4",
            output_path,
        ]

        command = generate_sample_video_command(
            requested_streams,
            output_path,
            container='mp4',
        )

        self.assertEqual(command, expected_command)

    def test_generate_sample_video(self):
        output_path = os.path.join(self.tmp_dir, 'output.mkv')
        requested_streams = [codec_name for codec_type, codec_name in self.ALMOST_ALL_STREAMS]

        generate_sample_video(
            requested_streams,
            output_path,
            container='matroska',
        )

        self.assertTrue(os.path.isfile(output_path))

        metadata = meta.get_metadata(output_path)
        self.assertIn('streams', metadata)

        streams = [
            (stream_metadata.get('codec_type'), stream_metadata.get('codec_name'))
            for stream_metadata in metadata['streams']
        ]
        self.assertEqual(streams, self.ALMOST_ALL_STREAMS)
