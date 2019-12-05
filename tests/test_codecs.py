import sys
import pytest
from unittest import TestCase

import ffmpeg_tools as ffmpeg


class TestSupportedConversions(TestCase):

    def test_list_video_conversion(self):
        assert( len( ffmpeg.codecs.list_supported_video_conversions("h264") ) > 1 )

    def test_list_video_conversion_invalid_codec(self):
        assert( len( ffmpeg.codecs.list_supported_video_conversions("blabla") ) == 0 )

    def test_list_audio_conversion(self):
        assert( len( ffmpeg.codecs.list_supported_audio_conversions("mp3") ) >= 1 )

    def test_list_audio_conversion_invalid_codec(self):
        assert( len( ffmpeg.codecs.list_supported_audio_conversions("blabla") ) == 0 )

    def test_can_convert_correct_video_codec(self):
        assert "h264" in ffmpeg.codecs._VIDEO_SUPPORTED_CONVERSIONS["h264"]
        self.assertTrue(ffmpeg.codecs.VideoCodec("h264").can_convert("h264"))

    def test_can_convert_unsupported_video_codec(self):
        assert "msmpeg4v2" not in ffmpeg.codecs._VIDEO_SUPPORTED_CONVERSIONS["h264"]
        self.assertFalse(ffmpeg.codecs.VideoCodec("h264").can_convert("msmpeg4v2"))


class TestGettingEncoder(TestCase):

    def test_valid_video_codec(self):
        assert(ffmpeg.codecs.get_video_encoder("h264") == "libx264")

    def test_invalid_video_codec(self):
        with self.assertRaises(ffmpeg.exceptions.UnsupportedVideoCodec):
            ffmpeg.codecs.get_video_encoder("bla")

    def test_valid_audio_codec(self):
        assert(ffmpeg.codecs.get_audio_encoder("mp3") == "libmp3lame")

    def test_invalid_audio_codec(self):
        with self.assertRaises(ffmpeg.exceptions.UnsupportedAudioCodec):
            ffmpeg.codecs.get_audio_encoder("bla")
