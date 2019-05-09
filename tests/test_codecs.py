import sys
import pytest
from unittest import TestCase

import ffmpeg_tools as ffmpeg
# import ffmpeg_tools.codecs as codecs
# import ffmpeg_tools.validation as validation


class TestSupportedConversions(TestCase):

    def test_list_video_conversion(self):
        assert( len( ffmpeg.codecs.list_supported_video_conversions("h264") ) > 1 )

    def test_list_video_conversion_invalid_codec(self):
        assert( len( ffmpeg.codecs.list_supported_video_conversions("blabla") ) == 0 )

    def test_list_audio_conversion(self):
        assert( len( ffmpeg.codecs.list_supported_audio_conversions("mp3") ) >= 1 )

    def test_list_audio_conversion_invalid_codec(self):
        assert( len( ffmpeg.codecs.list_supported_audio_conversions("blabla") ) == 0 )


class TestGettingEncoder(TestCase):

    def test_valid_video_codec(self):
        assert(ffmpeg.codecs.get_video_encoder("h264") == "libx264")

    def test_invalid_video_codec(self):
        with self.assertRaises(ffmpeg.validation.UnsupportedVideoCodec):
            ffmpeg.codecs.get_video_encoder("bla")

    def test_valid_audio_codec(self):
        assert(ffmpeg.codecs.get_audio_encoder("mp3") == "libmp3lame")

    def test_invalid_audio_codec(self):
        with self.assertRaises(ffmpeg.validation.UnsupportedAudioCodec):
            ffmpeg.codecs.get_audio_encoder("bla")