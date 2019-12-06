from unittest import TestCase, mock

from ffmpeg_tools import codecs
from ffmpeg_tools import exceptions
from ffmpeg_tools import validation


class TestSupportedConversions(TestCase):

    def test_list_video_conversion(self):
        assert len(codecs.list_supported_video_conversions("h264")) > 1

    def test_list_video_conversion_invalid_codec(self):
        assert len(codecs.list_supported_video_conversions("blabla")) == 0

    def test_list_audio_conversion(self):
        assert len(codecs.list_supported_audio_conversions("mp3")) >= 1

    def test_list_audio_conversion_invalid_codec(self):
        assert len(codecs.list_supported_audio_conversions("blabla")) == 0

    @mock.patch.dict('ffmpeg_tools.codecs._VIDEO_SUPPORTED_CONVERSIONS', {"h264": ["h264", "mjpeg", "vp9"]})
    def test_can_convert_correct_video_codec(self):
        self.assertTrue(codecs.VideoCodec("h264").can_convert("h264"))

    @mock.patch.dict('ffmpeg_tools.codecs._VIDEO_SUPPORTED_CONVERSIONS', {"h264": ["h264", "mjpeg", "vp9"]})
    def test_can_convert_unsupported_video_codec(self):
        self.assertFalse(codecs.VideoCodec("h264").can_convert("msmpeg4v2"))

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_SUPPORTED_CONVERSIONS', {"aac": ["aac", "mp3", "vorbis"]})
    def test_can_convert_correct_audio_codec(self):
        self.assertTrue(codecs.AudioCodec("aac").can_convert("aac"))

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_SUPPORTED_CONVERSIONS', {"aac": ["aac", "mp3", "vorbis"]})
    def test_can_convert_unsupported_audio_codec(self):
        self.assertFalse(codecs.AudioCodec("aac").can_convert("wmapro"))


class TestGettingEncoder(TestCase):

    def test_valid_video_codec(self):
        assert codecs.get_video_encoder("h264") == "libx264"

    def test_invalid_video_codec(self):
        with self.assertRaises(exceptions.UnsupportedVideoCodec):
            codecs.get_video_encoder("bla")

    def test_valid_audio_codec(self):
        assert codecs.get_audio_encoder("mp3") == "libmp3lame"

    def test_invalid_audio_codec(self):
        with self.assertRaises(exceptions.UnsupportedAudioCodec):
            codecs.get_audio_encoder("bla")
