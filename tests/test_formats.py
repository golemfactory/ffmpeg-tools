import sys
import pytest
from unittest import TestCase

import ffmpeg_tools as ffmpeg


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


class TestResolutionsTools(object):

    def test_listing(self):
        resolution_list = ffmpeg.formats.list_matching_resolutions( [1920, 1080] )
        assert( len( resolution_list ) > 2 )

    def test_listing2(self):
        resolution_list = ffmpeg.formats.list_matching_resolutions( [1280, 720] )
        assert( len( resolution_list ) > 2 )

    def test_listing_bad_propotions(self):
        resolution_list = ffmpeg.formats.list_matching_resolutions( [2, 1] )

        # Function returns at least resolution, that was passed in parameter.
        assert( len( resolution_list ) == 1 )

