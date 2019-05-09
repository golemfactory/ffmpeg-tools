import sys
import pytest

import ffmpeg_tools as ffmpeg


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

