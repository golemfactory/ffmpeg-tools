import sys
import pytest
from unittest import TestCase

import ffmpeg_tools as ffmpeg
from parameterized import parameterized


class TestContainer(TestCase):

    def test_get_demuxer_should_return_demuxer_from_demuxer_map(self):
        assert ffmpeg.formats.Container.c_WEBM in ffmpeg.formats._DEMUXER_MAP

        self.assertEqual(
            ffmpeg.formats.Container.c_WEBM.get_demuxer(),
            ffmpeg.formats.Container.c_MATROSKA_WEBM_DEMUXER.value)

    def test_get_demuxer_should_return_muxer_if_not_present_in_demuxer_map(self):
        assert ffmpeg.formats.Container.c_AVI not in ffmpeg.formats._DEMUXER_MAP

        self.assertEqual(
            ffmpeg.formats.Container.c_AVI.get_demuxer(),
            ffmpeg.formats.Container.c_AVI.value)

    def test_get_demuxer_should_work_when_used_with_an_exclusive_demuxer(self):
        assert ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER in ffmpeg.formats._EXCLUSIVE_DEMUXERS

        self.assertEqual(
            ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER.get_demuxer(),
            ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER.value)

    def test_is_exclusive_demuxer_should_return_values_based_on_exclusive_demuxers_dict(self):
        assert ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER in ffmpeg.formats._EXCLUSIVE_DEMUXERS
        assert ffmpeg.formats.Container.c_MOV not in ffmpeg.formats._EXCLUSIVE_DEMUXERS

        self.assertTrue(ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER.is_exclusive_demuxer())
        self.assertFalse(ffmpeg.formats.Container.c_MOV.is_exclusive_demuxer())

    def test_get_matching_muxers_should_return_all_matching_muxers(self):
        assert ffmpeg.formats.Container.c_MATROSKA_WEBM_DEMUXER in ffmpeg.formats._DEMUXER_MAP.values()
        assert ffmpeg.formats.Container.c_MATROSKA_WEBM_DEMUXER not in ffmpeg.formats._DEMUXER_MAP

        self.assertEqual(
            ffmpeg.formats.Container.c_MATROSKA_WEBM_DEMUXER.get_matching_muxers(),
            {ffmpeg.formats.Container.c_MATROSKA, ffmpeg.formats.Container.c_WEBM})

    def test_get_matching_muxers_should_return_muxer_itself_if_not_present_in_muxer_map(self):
        assert ffmpeg.formats.Container.c_AVI not in ffmpeg.formats._DEMUXER_MAP

        self.assertEqual(
            ffmpeg.formats.Container.c_AVI.get_matching_muxers(),
            {ffmpeg.formats.Container.c_AVI})

    def test_get_matching_muxers_should_never_return_exclusive_demuxers(self):
        assert ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER in ffmpeg.formats._EXCLUSIVE_DEMUXERS

        self.assertNotIn(
            ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER,
            ffmpeg.formats.Container.c_QUICK_TIME_DEMUXER.get_matching_muxers())

    def test_get_intermediate_muxer_should_return_values_from_safe_intermediate_formats_dict(self):
        demuxer = ffmpeg.formats.Container.c_MATROSKA_WEBM_DEMUXER
        assert demuxer in ffmpeg.formats._SAFE_INTERMEDIATE_FORMATS

        expected_intermediate_muxer = ffmpeg.formats._SAFE_INTERMEDIATE_FORMATS[demuxer]

        self.assertEqual(
            demuxer.get_intermediate_muxer(),
            expected_intermediate_muxer.value)

    def test_get_intermediate_muxer_should_return_self_if_demuxer_not_present_in_safe_intermediate_formats_dict(self):
        demuxer = ffmpeg.formats.Container.c_AVI
        assert demuxer not in ffmpeg.formats._SAFE_INTERMEDIATE_FORMATS

        expected_intermediate_muxer = demuxer

        self.assertEqual(
            demuxer.get_intermediate_muxer(),
            expected_intermediate_muxer.value)


class TestSupportedFormats(object):

    def test_existing_format(self):
        assert(ffmpeg.formats.is_supported("mp4") == True)

    def test_not_existing_format(self):
        assert(ffmpeg.formats.is_supported("bla") == False)


class TestListingSupportedFormats(object):

    def test_example_format(self):
        assert( "mp4" in ffmpeg.formats.list_supported_formats() )


class TestSupportedVideoCodecs(object):

    def test_existing_format(self):
        assert(ffmpeg.formats.is_supported_video_codec("mp4", "h264") == True)

    def test_not_existing_format(self):
        assert(ffmpeg.formats.is_supported_video_codec("bla", "h264") == False)

    def test_not_existing_codec(self):
        assert(ffmpeg.formats.is_supported_video_codec("mp4", "bla") == False)

    def test_container_is_supported(self):
        container = ffmpeg.formats.Container("mp4")
        vcodec = "h264"
        vcodec_class = ffmpeg.codecs.VideoCodec(vcodec)

        assert container.is_supported_video_codec(vcodec)
        assert container.is_supported_video_codec(vcodec_class)
        assert not container.is_supported_video_codec("bla")


class TestListingSupportedVideoCodecs(object):

    def test_existing_format(self):
        assert( len( ffmpeg.formats.list_supported_video_codecs("mp4") ) != 0 )

    def test_not_existing_format(self):
        assert( len( ffmpeg.formats.list_supported_video_codecs("bla") ) == 0 )


class TestSupportedAudioCodecs(object):

    def test_existing_format(self):
        assert(ffmpeg.formats.is_supported_audio_codec("mp4", "mp3") == True)

    def test_not_existing_format(self):
        assert(ffmpeg.formats.is_supported_audio_codec("bla", "mp3") == False)

    def test_not_existing_codec(self):
        assert(ffmpeg.formats.is_supported_audio_codec("mp4", "bla") == False)

    def test_container_is_supported(self):
        container = ffmpeg.formats.Container("mp4")
        acodec = "mp3"
        acodec_class = ffmpeg.codecs.AudioCodec(acodec)

        assert container.is_supported_audio_codec(acodec)
        assert container.is_supported_audio_codec(acodec_class)
        assert not container.is_supported_audio_codec("bla")


class TestAspectRatioCalculations(TestCase):

    @parameterized.expand([
        ([333, 333], "1:1"),
        ([333, 666], "1:2"),
        ([1366, 768], "16:9"),
        ([1360, 768], "16:9"),
        ([1920, 1080], "16:9"),
        ([2560, 1080], "21:9"),
        ([3440, 1440], "21:9"),
    ])
    def test_effective_aspect_ratio(self, resolution, expected_aspect_ratio):
        aspect_ratio = ffmpeg.formats.get_effective_aspect_ratio(resolution)
        self.assertEqual(aspect_ratio, expected_aspect_ratio)

    @parameterized.expand([
        ([333, 666], "1:2"),
        ([1024, 768], "4:3"),
        ([1920, 1080], "16:9"),
        ([1280, 1024], "5:4"),
        ([1360, 768], "85:48"),
        ([1366, 768], "683:384"),
        ([2560, 1080], "64:27"),
        ([3440, 1440], "43:18"),
    ])
    def test_calculate_aspect_ratio(self, resolution, expected_aspect_ratio):
        aspect_ratio = ffmpeg.formats.calculate_aspect_ratio(resolution)
        self.assertEqual(aspect_ratio, expected_aspect_ratio)


class TestHelperFunctions(TestCase):

    def test_get_safe_intermediate_format_for_demuxer(self):
        demuxer = ffmpeg.formats.Container.c_AVI
        self.assertEqual(
            ffmpeg.formats.get_safe_intermediate_format_for_demuxer(demuxer),
            demuxer.get_intermediate_muxer())

class TestFrameRate(TestCase):
    def test_should_have_a_default_for_divisor(self):
        self.assertEqual(ffmpeg.formats.FrameRate(10), (10, 1))
        self.assertEqual(ffmpeg.formats.FrameRate(10, 5), (10, 5))
        self.assertEqual(ffmpeg.formats.FrameRate(10, 6), (10, 6))
