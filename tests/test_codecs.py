from unittest import TestCase, mock

from ffmpeg_tools import codecs
from ffmpeg_tools import exceptions
from ffmpeg_tools import formats
from ffmpeg_tools import utils
from ffmpeg_tools import validation


class TestAudioCodec(TestCase):
    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'aac': None})
    def test_is_supported_sample_rate_should_return_false_if_codec_does_not_have_encoder(self):
        self.assertFalse(codecs.AudioCodec.AAC.is_supported_sample_rate(5000, None))
        self.assertFalse(codecs.AudioCodec.AAC.is_supported_sample_rate(48000, None))

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'aac': 'aac'})
    def test_is_supported_sample_rate_should_use_encoder_info_if_available(self):
        encoder_info = {'sample_rates': [5000, 48000]}
        self.assertTrue(codecs.AudioCodec.AAC.is_supported_sample_rate(5000, encoder_info))
        self.assertTrue(codecs.AudioCodec.AAC.is_supported_sample_rate(48000, encoder_info))
        self.assertFalse(codecs.AudioCodec.AAC.is_supported_sample_rate(6000, encoder_info))

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'aac': 'aac'})
    def test_is_supported_sample_rate_should_return_false_if_supported_sample_rates_cannot_be_determined(self):
        self.assertFalse(codecs.AudioCodec.AAC.is_supported_sample_rate(5000, None))
        self.assertFalse(codecs.AudioCodec.AAC.is_supported_sample_rate(48000, None))


class TestSubtitleCodec(TestCase):
    def test_missing(self):
        assert 'unsupported codec' not in codecs.SubtitleCodec._value2member_map_

        with self.assertRaises(exceptions.UnsupportedSubtitleCodec):
            codecs.SubtitleCodec('unsupported codec')

    def test_from_name(self):
        assert codecs.SubtitleCodec.SUBRIP.value == 'subrip'

        self.assertEqual(codecs.SubtitleCodec('subrip'), codecs.SubtitleCodec.SUBRIP)

    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_get_supported_conversions(self):
        self.assertCountEqual(codecs.SubtitleCodec.SUBRIP.get_supported_conversions(), ['subrip', 'ass', 'webvtt'])


class TestSupportedConversions(TestCase):

    def test_list_video_conversion(self):
        assert len(codecs.list_supported_video_conversions("h264")) > 1

    def test_list_video_conversion_invalid_codec(self):
        assert len(codecs.list_supported_video_conversions("blabla")) == 0

    def test_list_audio_conversion(self):
        assert len(codecs.list_supported_audio_conversions("mp3")) >= 1

    def test_list_audio_conversion_invalid_codec(self):
        assert len(codecs.list_supported_audio_conversions("blabla")) == 0

    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_list_subtitle_conversion(self):
        assert len(codecs.list_supported_subtitle_conversions("subrip")) > 1

    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_list_subtitle_conversion_invalid_codec(self):
        assert len(codecs.list_supported_subtitle_conversions("blabla")) == 0

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

    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_can_convert_correct_subtitle_codec(self):
        self.assertTrue(codecs.SubtitleCodec("subrip").can_convert("subrip"))

    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_can_convert_unsupported_subtitle_codec(self):
        self.assertFalse(codecs.SubtitleCodec("subrip").can_convert("mov_text"))

    @mock.patch.dict('ffmpeg_tools.formats._CONTAINER_SUPPORTED_CODECS', {"matroska": {'subtitlecodecs': ['subrip', 'ass']}})
    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_select_conversion_for_container(self):
        assert formats.is_supported(formats.Container.c_MOV.value)

        self.assertEqual(
            codecs.SubtitleCodec.SUBRIP.select_conversion_for_container(formats.Container.c_MATROSKA.value),
            codecs.SubtitleCodec.ASS.value,
        )

    @mock.patch.dict('ffmpeg_tools.formats._CONTAINER_SUPPORTED_CODECS', {"mov": {'subtitlecodecs': ['mov_text']}})
    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {'subrip': ['subrip', 'ass', 'webvtt']})
    def test_select_conversion_for_container_should_return_none_if_target_container_does_not_support_any_conversion_target(self):
        self.assertEqual(
            codecs.SubtitleCodec.SUBRIP.select_conversion_for_container(formats.Container.c_MOV.value),
            None,
        )

    def test_select_conversion_for_container_should_return_none_if_target_container_is_not_supported(self):
        assert not formats.is_supported('invalid container')

        self.assertEqual(
            codecs.SubtitleCodec.SUBRIP.select_conversion_for_container('invalid container'),
            None,
        )


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


class TestIsSupportedSampleRate(TestCase):
    def test_is_supported_sample_rate_should_ask_audio_codec_if_codec_supported(self):
        with mock.patch.object(codecs.AudioCodec, 'is_supported_sample_rate', return_value=True):
            self.assertEqual(codecs.is_supported_sample_rate("aac", 5000, {}), True)

        with mock.patch.object(codecs.AudioCodec, 'is_supported_sample_rate', return_value=False):
            self.assertEqual(codecs.is_supported_sample_rate("aac", 5000, {}), False)

    def test_is_sample_rate_supported_should_return_false_if_codec_not_supported(self):
        assert 'abcdef' not in codecs.AudioCodec._value2member_map_

        with mock.patch.object(codecs.AudioCodec, 'is_supported_sample_rate', return_value=True):
            self.assertEqual(codecs.is_supported_sample_rate("abcdef", 5000, {}), False)

        with mock.patch.object(codecs.AudioCodec, 'is_supported_sample_rate', return_value=False):
            self.assertEqual(codecs.is_supported_sample_rate("abcdef", 5000, {}), False)
