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


    @mock.patch('ffmpeg_tools.commands.find_unsupported_data_streams', return_value=[2])
    @mock.patch('ffmpeg_tools.commands.find_unsupported_subtitle_streams', return_value=[3])
    def test_replace_streams_command_removes_streams_not_in_whitelist_if_asked_to(
        self,
        _mock_find_unsupported_subtitle_streams,
        _mock_find_unsupported_data_streams,
    ):
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


class TestUnsupportedStreamDetection(TestCase):
    METADATA_WITH_SUBTITLES = {
        'streams': [
            {'index': 2, 'codec_type': 'video', 'codec_name': 'h264'},
            {'index': 6, 'codec_type': 'audio', 'codec_name': 'aac'},
            {'index': 3, 'codec_type': 'subtitle', 'codec_name': 'subrip'},
            {'index': 8, 'codec_type': 'subtitle', 'codec_name': 'ass'},
            {'index': 4, 'codec_type': 'subtitle', 'codec_name': 'mov_text'},
            {'index': 1, 'codec_type': 'subtitle', 'codec_name': 'webvtt'},
            {'index': 9, 'codec_type': 'subtitle', 'codec_name': 'some unsupported codec'},
            {'index': 0, 'codec_type': 'data', 'codec_name': 'bin_data'},
            {'index': 7, 'codec_type': 'weird unsupported codec type', 'codec_name': 'subrip'},
            {'index': 10, 'codec_type': 'data', 'codec_name': 'dvd_nav_packet'},
        ]
    }

    @mock.patch.object(codecs, 'DATA_STREAM_WHITELIST', ["dvd_nav_packet"])
    def test_find_unsupported_data_streams_strips_non_whitelisted_streams(self):
        self.assertCountEqual(commands.find_unsupported_data_streams(self.METADATA_WITH_SUBTITLES), [0])

    @mock.patch.dict('ffmpeg_tools.formats._CONTAINER_SUPPORTED_CODECS', {"matroska": {'subtitlecodecs': ['mov_text']}})
    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {
        'subrip': ['subrip', 'ass', 'mov_text'],
        'ass': ['ass', 'mov_text'],
        'mov_text': ['mov_text'],
        'webvtt': ['subrip', 'ass'],
    })
    def test_find_unsupported_subtitle_streams_strips_streams_not_convertible_to_something_supported_by_target_container(self):
        self.assertCountEqual(
            commands.find_unsupported_subtitle_streams(
                self.METADATA_WITH_SUBTITLES,
                formats.Container.c_MATROSKA.value,
             ),
             [1, 9],
         )

    def test_find_unsupported_subtitle_streams_does_not_strip_streams_if_target_container_is_not_specified(self):
        self.assertEqual(
            commands.find_unsupported_subtitle_streams(self.METADATA_WITH_SUBTITLES, None),
            [],
        )


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
