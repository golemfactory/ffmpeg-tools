import copy
import os
import tempfile

from unittest import TestCase, mock
import ffmpeg_tools as ffmpeg
from ffmpeg_tools import codecs
from ffmpeg_tools import commands
from ffmpeg_tools.codecs import DATA_STREAM_WHITELIST, SUBTITLE_STREAM_WHITELIST
from ffmpeg_tools.commands import get_lists_of_unsupported_stream_numbers
from tests.test_meta import example_metadata

BIN_DATA_EXAMPLE_STREAM = {
    'index': 2,
    'codec_name': DATA_STREAM_WHITELIST[0],
    'codec_long_name': 'binary data',
    'profile': 'unknown',
    'codec_type': 'data',
    'codec_tag_string': '[6][0][0][0]',
    'codec_tag': '0x0006',
    'id': '0x102',
    'r_frame_rate': '0 / 0',
    'avg_frame_rate': '0 / 0',
    'time_base': 1 / 90000,
    'start_pts': 131920,
    'start_time': 1.465778,
    'duration_ts': 475200,
    'duration': 5.280000,
    'bit_rate': 'N/A',
    'max_bit_rate': 'N/A',
    'bits_per_raw_sample': 'N/A',
    'nb_frames': 'N/A',
    'nb_read_frames': 'N/A',
    'nb_read_packets': 'N/A',
}

SUBTITLES_EXAMPLE_STREAM = {
    'index': 3,
    'codec_name': SUBTITLE_STREAM_WHITELIST[0],
    'codec_long_name': 'SubRip subtitle',
    'codec_type': 'subtitle',
    'codec_time_base': '0/1',
    'codec_tag_string': '[0][0][0][0]',
    'codec_tag': '0x0000',
    'r_frame_rate': '0/0',
    'avg_frame_rate': '0/0',
    'time_base': '1/1000',
    'start_pts': 0, 'start_time': '0.000000',
    'duration_ts': 46665,
    'duration': '46.665000',
    'disposition': {
        'default': 1, 'dub': 0,
        'original': 0, 'comment': 0,
        'lyrics': 0, 'karaoke': 0,
        'forced': 0,
        'hearing_impaired': 0,
        'visual_impaired': 0,
        'clean_effects': 0,
        'attached_pic': 0,
        'timed_thumbnails': 0},
    'tags': {'language': 'eng'}}


class TestCommands(TestCase):

    def test_transcoding(self):
        params = ffmpeg.meta.create_params("mp4", [1280, 800], "h265")

        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        output_video = os.path.join(tempfile.gettempdir(), "ForBiggerBlazes-[codec=h265].mp4")

        if os.path.exists(output_video):
            os.remove(output_video)

        ffmpeg.commands.transcode_video(input_video, params, output_video)

        assert os.path.exists(output_video)


    def test_get_video_length(self):
        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        length = ffmpeg.commands.get_video_len(input_video)

        assert length == 15.021667


    def test_failed_command(self):
        with self.assertRaises(ffmpeg.commands.CommandFailed):
            ffmpeg.commands.get_video_len("bla")


    def test_transcode_video_command(self):
        command = commands.transcode_video_command(
            "input.mp4",
            "output.mkv",
            {
                'container': 'matroska',
                'frame_rate': '25/1',
                'video': {
                    'codec': 'h264',
                    'bitrate': '1000k',
                },
                'resolution': [1920, 1080],
                'scaling_alg': 'neighbor',
            },
        )

        expected_command = [
            "ffmpeg",
            "-nostdin",
            "-i", "input.mp4",
            "-f", "matroska",
            "-c:v", codecs.VideoCodec.get_encoder(codecs.VideoCodec.H_264),
            "-crf", "22",
            "-r", "25/1",
            "-b:v", "1000k",
            "-vf", "scale=1920:1080",
            "-sws_flags", "neighbor",
            "output.mkv",
        ]
        self.assertEqual(command, expected_command)


    def test_transcode_video_command_with_optional_values_missing(self):
        command = commands.transcode_video_command(
            "input.mp4",
            "output.mkv",
            {},
        )

        expected_command = [
            "ffmpeg",
            "-nostdin",
            "-i", "input.mp4",
            "output.mkv",
        ]
        self.assertEqual(command, expected_command)


    def test_replace_streams_command(self):
        command = ffmpeg.commands.replace_streams_command(
            "tests/resources/ForBiggerBlazes-[codec=h264].mp4",
            "tests/resources/ForBiggerBlazes-[codec=h264][video-only].mkv",
            "tests/resources/ForBiggerBlazes-[codec=h264].mkv",
            "v",
            {
                'audio': {
                    'codec': 'mp3',
                    'bitrate': '128k',
                }
            },
        )

        expected_command = [
            "ffmpeg",
            "-nostdin",
            "-i", "tests/resources/ForBiggerBlazes-[codec=h264].mp4",
            "-i", "tests/resources/ForBiggerBlazes-[codec=h264][video-only].mkv",
            "-map", "1:v",
            "-map", "0",
            "-map", "-0:v",
            "-copy_unknown",
            "-c:v", "copy",
            "-c:d", "copy",
            "-c:a", codecs.AudioCodec.get_encoder(codecs.AudioCodec.MP3),
            "-b:a", "128k",
            "tests/resources/ForBiggerBlazes-[codec=h264].mkv",
        ]
        self.assertEqual(command, expected_command)


    def test_replace_streams_command_validates_stream_type(self):
        with self.assertRaises(ffmpeg.commands.InvalidArgument):
            ffmpeg.commands.replace_streams_command(
                "tests/resources/ForBiggerBlazes-[codec=h264].mp4",
                "tests/resources/ForBiggerBlazes-[codec=h264][video-only].mkv",
                "tests/resources/ForBiggerBlazes-[codec=h264].mkv",
                "v:1",
                {},
            )

    def test_replace_streams_command_removes_streams_not_in_whitelist(self):
        with mock.patch('ffmpeg_tools.commands.get_lists_of_unsupported_stream_numbers') as _get_lists_of_unsupported_streams_numbers:

            _get_lists_of_unsupported_streams_numbers.return_value = ([2], [3])

            command = ffmpeg.commands.replace_streams_command(
                "tests/resources/ForBiggerBlazes-[codec=h264].mp4",
                "tests/resources/ForBiggerBlazes-[codec=h264][video-only].mkv",
                "tests/resources/ForBiggerBlazes-[codec=h264].mkv",
                "v",
                {},
                strip_unsupported_data_streams=True,
                strip_unsupported_subtitle_streams=True
            )

            expected_command = [
                "ffmpeg",
                "-nostdin",
                "-i", "tests/resources/ForBiggerBlazes-[codec=h264].mp4",
                "-i", "tests/resources/ForBiggerBlazes-[codec=h264][video-only].mkv",  # noqa pylint:disable=line-too-long
                "-map", "1:v",
                "-map", "0",
                "-map", "-0:v",
                '-map', '-0:2',
                '-map', '-0:3',
                "-copy_unknown",
                "-c:v", "copy",
                "-c:d", "copy",
                "tests/resources/ForBiggerBlazes-[codec=h264].mkv",
            ]
            self.assertEqual(command, expected_command)


class MetadataWithSupportedAndUnsupportedStreamsBase(TestCase):

    def setUp(self):
        super().setUp()
        self.metadata_without_unsupported_streams = copy.deepcopy(
            example_metadata)
        self.metadata_without_unsupported_streams['streams'].extend(
            [BIN_DATA_EXAMPLE_STREAM, SUBTITLES_EXAMPLE_STREAM])
        self.metadata_without_unsupported_streams['format']['nb_streams'] = 4

        self.metadata_with_unsupported_streams = copy.deepcopy(
            self.metadata_without_unsupported_streams)

        assert 'some default unsupported name' not in BIN_DATA_EXAMPLE_STREAM
        assert 'some default unsupported name' not in SUBTITLES_EXAMPLE_STREAM

        self.metadata_with_unsupported_streams['streams'][2]['codec_name'] = \
            'some default unsupported name'
        self.metadata_with_unsupported_streams['streams'][3]['codec_name'] = \
            'some default unsupported name'


class TestGetListOfStreamNumbersToSkip(
    MetadataWithSupportedAndUnsupportedStreamsBase
):

    def test_function_does_not_strip_whitelisted_streams(self):
        stream_number = get_lists_of_unsupported_stream_numbers(
            self.metadata_without_unsupported_streams,
        )
        self.assertEqual(stream_number, ([], []))

    def test_function_strips_non_whitelisted_streams(self):
        stream_number = get_lists_of_unsupported_stream_numbers(
            self.metadata_with_unsupported_streams,
        )
        self.assertEqual(stream_number, ([2], [3]))

    def test_function_returns_correct_numbers_streams_metadata(self):
        stream_number = get_lists_of_unsupported_stream_numbers(
            self.metadata_with_unsupported_streams)
        self.assertEqual(stream_number, ([2], [3]))
