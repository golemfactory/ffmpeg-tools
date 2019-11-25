import copy
import os
import tempfile
from unittest import TestCase, mock

from parameterized import parameterized

from ffmpeg_tools import codecs
from ffmpeg_tools import commands
from ffmpeg_tools import exceptions
from ffmpeg_tools import formats
from ffmpeg_tools import meta
from tests.test_meta import example_metadata
from tests.utils import get_absolute_resource_path


BIN_DATA_EXAMPLE_STREAM = {
    'index': 2,
    'codec_name': codecs.DATA_STREAM_WHITELIST[0],
    'codec_long_name': 'binary data',
    'profile': 'unknown',
    'codec_type': 'data',
    'codec_tag_string': '[6][0][0][0]',
    'codec_tag': '0x0006',
    'id': '0x102',
    'r_frame_rate': '0/0',
    'avg_frame_rate': '0/0',
    'time_base': '1/90000',
    'start_pts': 131920,
    'start_time': '1.465778',
    'duration_ts': 475200,
    'duration': '5.280000',
    'bit_rate': 'N/A',
    'max_bit_rate': 'N/A',
    'bits_per_raw_sample': 'N/A',
    'nb_frames': 'N/A',
    'nb_read_frames': 'N/A',
    'nb_read_packets': 'N/A',
}

SUBTITLES_EXAMPLE_STREAM = {
    'index': 3,
    'codec_name': codecs.SUBTITLE_STREAM_WHITELIST[0],
    'codec_long_name': 'SubRip subtitle',
    'codec_type': 'subtitle',
    'codec_time_base': '0/1',
    'codec_tag_string': '[0][0][0][0]',
    'codec_tag': '0x0000',
    'r_frame_rate': '0/0',
    'avg_frame_rate': '0/0',
    'time_base': '1/1000',
    'start_pts': 0,
    'start_time': '0.000000',
    'duration_ts': 46665,
    'duration': '46.665000',
    'disposition': {
        'default': 1,
        'dub': 0,
        'original': 0,
        'comment': 0,
        'lyrics': 0,
        'karaoke': 0,
        'forced': 0,
        'hearing_impaired': 0,
        'visual_impaired': 0,
        'clean_effects': 0,
        'attached_pic': 0,
        'timed_thumbnails': 0
    },
    'tags': {
        'language': 'eng',
    }
}


class TestCommands(TestCase):

    def test_transcoding(self):
        params = meta.create_params("mp4", [1280, 800], "h265")

        input_video = get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4')
        output_video = os.path.join(tempfile.gettempdir(), "ForBiggerBlazes-[codec=h265].mp4")

        if os.path.exists(output_video):
            os.remove(output_video)

        commands.transcode_video(input_video, params, output_video)

        assert os.path.exists(output_video)


    def test_get_video_length(self):
        input_video = get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4')
        length = commands.get_video_len(input_video)

        assert length == 15.021667


    def test_failed_command(self):
        with self.assertRaises(exceptions.CommandFailed):
            commands.get_video_len("bla")


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


    def test_transcode_video_command_does_not_accept_audio_parameters(self):
        with self.assertRaises(exceptions.InvalidArgument):
            commands.transcode_video_command(
                "input.mp4",
                "output.mkv",
                {
                    'audio': {
                        'codec': 'mp3',
                        'bitrate': '128k',
                    },
                },
            )


    def test_replace_streams_command(self):
        command = commands.replace_streams_command(
            get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
            get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
            get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
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
            "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
            "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
            "-map", "1:v",
            "-map", "0",
            "-map", "-0:v",
            "-copy_unknown",
            "-c:v", "copy",
            "-c:d", "copy",
            "-c:a", codecs.AudioCodec.get_encoder(codecs.AudioCodec.MP3),
            "-b:a", "128k",
            get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
        ]
        self.assertEqual(command, expected_command)


    def test_replace_streams_command_validates_stream_type(self):
        with self.assertRaises(exceptions.InvalidArgument):
            commands.replace_streams_command(
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
                "v:1",
                {},
            )


    def test_replace_streams_command_removes_streams_not_in_whitelist(self):
        with mock.patch('ffmpeg_tools.commands.find_unsupported_data_streams') as _find_unsupported_data_streams, \
             mock.patch('ffmpeg_tools.commands.find_unsupported_subtitle_streams') as _find_unsupported_subtitle_streams:
            _find_unsupported_data_streams.return_value = [2]
            _find_unsupported_subtitle_streams.return_value = [3]

            command = commands.replace_streams_command(
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
                "v",
                {},
                strip_unsupported_data_streams=True,
                strip_unsupported_subtitle_streams=True
            )

            expected_command = [
                "ffmpeg",
                "-nostdin",
                "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
                "-i", get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
                "-map", "1:v",
                "-map", "0",
                "-map", "-0:v",
                '-map', '-0:2',
                '-map', '-0:3',
                "-copy_unknown",
                "-c:v", "copy",
                "-c:d", "copy",
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
            ]
            self.assertEqual(command, expected_command)


    def test_replace_streams_command_does_not_accept_video_parameters(self):
        with self.assertRaises(exceptions.InvalidArgument):
            commands.replace_streams_command(
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264][video-only].mkv'),
                get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mkv'),
                "v",
                {
                    'video': {
                        'codec': 'h264',
                        'bitrate': '1000k',
                    },
                }
            )


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


class TestUnsupportedStreamDetection(
    MetadataWithSupportedAndUnsupportedStreamsBase
):

    def test_function_does_not_strip_whitelisted_streams(self):
        stream_number = (
            commands.find_unsupported_data_streams(self.metadata_without_unsupported_streams),
            commands.find_unsupported_subtitle_streams(self.metadata_without_unsupported_streams),
        )
        self.assertEqual(stream_number, ([], []))

    def test_function_strips_non_whitelisted_streams(self):
        stream_number = (
            commands.find_unsupported_data_streams(self.metadata_with_unsupported_streams),
            commands.find_unsupported_subtitle_streams(self.metadata_with_unsupported_streams),
        )
        self.assertEqual(stream_number, ([2], [3]))


class TestQueryMuxerInfo(TestCase):

    def test_function_should_return_valid_encoder(self):
        sample_ffmpeg_output = (
            'Muxer 3g2 [3GP2 (3GPP2 file format)]:\n'
            '   Common extensions: 3g2.\n'
            '   Default video codec: h263.\n'
            '   Default audio codec: amr_nb.\n'
            'matroska muxer AVOptions:'
        )

        with mock.patch.object(commands, 'exec_cmd_to_string', return_value=sample_ffmpeg_output):
            muxer_info = commands.query_muxer_info(formats.Container.c_3G2)
            self.assertEqual(muxer_info['default_audio_codec'], 'amr_nb')

    def test_default_audio_codec_field_should_be_omitted_if_not_found_in_ffmpeg_output(self):
        sample_ffmpeg_output = (
            'Muxer 3g2 [3GP2 (3GPP2 file format)]:\n'
            '   Common extensions: 3g2.\n'
            '   Default video codec: h263.\n'
        )

        with mock.patch.object(commands, 'exec_cmd_to_string', return_value=sample_ffmpeg_output):
            muxer_info = commands.query_muxer_info(formats.Container.c_3G2)
            self.assertIsInstance(muxer_info, dict)
            self.assertNotIn('default_audio_codec', muxer_info)

    def test_default_audio_codec_field_should_be_omitted_if_multiple_matches_found_in_ffmpeg_output(self):
        sample_ffmpeg_output = (
            'Muxer 3g2 [3GP2 (3GPP2 file format)]:\n'
            '   Common extensions: 3g2.\n'
            '   Default video codec: h263.\n'
            '   Default audio codec: amr_nb.\n'
            '   Default audio codec: mp3.\n'
            '   Default audio codec: amr_nb.\n'
        )

        with mock.patch.object(commands, 'exec_cmd_to_string', return_value=sample_ffmpeg_output):
            with self.assertRaises(exceptions.NoMatchingEncoder):
                commands.query_muxer_info(formats.Container.c_3G2)

    def test_muxer_not_recognized_by_ffmpeg_should_result_in_default_audio_codec_not_being_found(self):
        muxer_info = commands.query_muxer_info('non_existent_container')
        self.assertIsInstance(muxer_info, dict)
        self.assertNotIn('default_audio_codec', muxer_info)

    def test_demuxer_should_result_in_default_audio_codec_not_being_found(self):
        muxer_info = commands.query_muxer_info(formats.Container.c_MATROSKA_WEBM_DEMUXER.value)
        self.assertIsInstance(muxer_info, dict)
        self.assertNotIn('default_audio_codec', muxer_info)

    @parameterized.expand([
        ('   Default audio codec: amr_nb.\n', ['amr_nb']),
        ('   Default audio codec: vorbis.\n', ['vorbis']),
        ('   Default audio codec: amr_nb\n', ['amr_nb']),
        ('Default audio codec: amr_nb.\n', ['amr_nb']),
        ('Default audio codec: amr_nb\n', ['amr_nb']),
        ('blabla Default audio codec: amr_nb.\n', []),
        ('Default audio codec: amr_nb.FAILED.\n', ['amr_nb.FAILED']),
        ('Default audiocodec: amr_nb.\n', ['amr_nb']),
        ('Default audio codec amr_nb.\n', []),
        ('Default audio codec: amr nb.\n', ['amr nb']),
        ('Default audio codec: amr_nb.\n', ['amr_nb']),
        ('Default audio codec: amr_nb_.\n', ['amr_nb_']),
        ('Default audio codec: amr_nb_\n', ['amr_nb_']),
        ('Default audio codec: amr_nb. Default audio codec: mp2 \n', ['amr_nb. Default audio codec: mp2']),
        ('    Default audio codec: amr_nb-x!\n', ['amr_nb-x!']),
    ])
    def test_default_audio_encoder_parsing_corner_cases(
        self,
        input_line,
        expected_result,
    ):
        text = (
            f'some text before sample line \n'
            f'{input_line}'
            f'some text after sample line \n'
        )
        result = commands._parse_default_audio_codec_out_of_muxer_info(text)
        self.assertEqual(result, expected_result)
