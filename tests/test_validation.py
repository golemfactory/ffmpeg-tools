from unittest import TestCase
import sys

from ffmpeg_tools.formats import list_supported_formats, list_supported_video_codecs, list_supported_audio_codecs
from ffmpeg_tools.meta import get_metadata
from ffmpeg_tools.validation import UnsupportedVideoCodec, UnsupportedVideoFormat, \
    UnsupportedTargetVideoFormat, MissingVideoStream, UnsupportedAudioCodec, \
    InvalidVideo, MissingVideoStream, InvalidFormatMetadata

import ffmpeg_tools.validation as validation
import ffmpeg_tools.formats as formats
import ffmpeg_tools.meta as meta
from parameterized import parameterized


class TestInputValidation(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._filename = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        cls._metadata = get_metadata(cls._filename)
        cls._supported_formats = list_supported_formats()
        cls._format_metadata = {"format_name": "mov", "duration": "10"}
        cls._audio_stream = {"codec_name": "mp3", "codec_type": "audio"}
        cls._video_stream = {"codec_name": "h264", "codec_type": "video", "width": 800, "height": 600}
        cls._test_metadata = {
            "streams": [cls._audio_stream, cls._video_stream],
            "format": cls._format_metadata
        }

    def setUp(self) -> None:
        pass


    def test_validate_valid_video_format(self):
        for video_format in self._supported_formats:
            self.assertTrue(validation.validate_format(video_format))


    def test_validate_invalid_video_format(self):
        with self.assertRaises(UnsupportedVideoFormat):
            validation.validate_format("jpg")


    def test_validate_target_format_should_accept_muxers(self):
        assert not formats.Container.c_MP4.is_exclusive_demuxer()

        self.assertTrue(validation.validate_target_format(formats.Container.c_MP4.value))


    def test_validate_target_format_should_reject_exclusive_demuxers(self):
        assert formats.Container.c_QUICK_TIME_DEMUXER.is_exclusive_demuxer()

        with self.assertRaises(UnsupportedTargetVideoFormat):
            validation.validate_target_format(formats.Container.c_QUICK_TIME_DEMUXER.value)


    def test_validate_valid_video_codecs(self):
        for video_format in self._supported_formats:
            supported_video_codecs = list_supported_video_codecs(video_format)
            for video_codec in supported_video_codecs:
                self.assertTrue(validation.validate_video_codec(video_codec=video_codec, video_format=video_format))


    def test_validate_invalid_video_codec(self):
        with self.assertRaises(UnsupportedVideoCodec):
            validation.validate_video_codec(video_codec="unknown", video_format="mp4")


    def test_validate_valid_audio_codecs(self):
        for video_format in self._supported_formats:
            supported_audio_codecs = list_supported_audio_codecs(video_format)
            for audio_codec in supported_audio_codecs:
                self.assertTrue(validation.validate_audio_codec(audio_codec=audio_codec, video_format=video_format))


    def test_validate_invalid_audio_codec(self):
        with self.assertRaises(UnsupportedAudioCodec):
            validation.validate_audio_codec(audio_codec="unknown", video_format="mp4")


    def test_validate_audio_stream_valid_codecs(self):
        for video_format in self._supported_formats:
            supported_audio_codecs = list_supported_audio_codecs(video_format)
            for audio_codec in supported_audio_codecs:
                self.assertTrue(validation.validate_audio_stream(stream_metadata={"codec_name": "{}".format(audio_codec)},
                                                      video_format=video_format))


    def test_validate_audio_stream_invalid_codec(self):
        with self.assertRaises(UnsupportedAudioCodec):
            validation.validate_audio_stream(stream_metadata={"codec_name": "unknown"}, video_format="mp4")


    def test_validate_audio_stream_without_codec(self):
        with self.assertRaises(InvalidVideo):
            validation.validate_audio_stream(stream_metadata={}, video_format="mp4")


    def test_validate_video_stream_valid_codecs(self):
        for video_format in self._supported_formats:
            supported_video_codecs = list_supported_video_codecs(video_format)
            for video_codec in supported_video_codecs:
                self.assertTrue(validation.validate_video_stream(stream_metadata={"codec_name": "{}".format(video_codec)},
                                                      video_format=video_format))

    def test_validate_video_stream_invalid_codec(self):
        with self.assertRaises(UnsupportedVideoCodec):
            validation.validate_video_stream(stream_metadata={"codec_name": "unknown"}, video_format="mp4")


    def test_validate_video_stream_without_codec(self):
        with self.assertRaises(InvalidVideo):
            validation.validate_audio_stream(stream_metadata={}, video_format="mp4")


    def test_validate_video_stream_existence_without_video_stream(self):
        with self.assertRaises(MissingVideoStream):
            validation.validate_video_stream_existence(metadata={"streams": [{"codec_type": "audio"}]})


    def test_validate_video_stream_no_streams_key(self):
        with self.assertRaises(InvalidVideo):
            validation.validate_video_stream_existence(metadata={})


    def test_validate_video_contains_video_stream(self):
        self.assertTrue(validation.validate_video_stream_existence(metadata={"streams": [{"codec_type": "video"}]}))


    def test_validate_format_metadata_without_missing_format_metadata(self):
        with self.assertRaises(InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={})

        with self.assertRaises(InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={"format": {}})


    def test_validate_format_metadata_empty_format_names(self):
        with self.assertRaises(InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={"format": {"format_name": ""}})


    def test_validate_format_metadata(self):
        self.assertTrue(validation.validate_format_metadata(metadata={"format": self._format_metadata}))


    def test_validate_video_invalid_format(self):
        metadata = dict(self._metadata)
        metadata["format"] = {"format_name": "jpeg"}

        with self.assertRaises(UnsupportedVideoFormat):
            validation.validate_video(metadata=metadata)


    def test_validate_video_valid_codecs(self):
        for video_format in self._supported_formats:
            video_codecs = list_supported_video_codecs(video_format)
            audio_codecs = list_supported_audio_codecs(video_format)
            for video_codec in video_codecs:
                for audio_codec in audio_codecs:
                    metadata = {
                        "format": {"format_name": video_format},
                        "streams": [
                            {
                                "codec_type": "video",
                                "codec_name": video_codec
                            },
                            {
                                "codec_type": "audio",
                                "codec_name": audio_codec
                            }
                        ]
                    }

                    self.assertTrue(validation.validate_video(metadata=metadata))


    def test_validate_video_invalid_audio_codec(self):
        with self.assertRaises(UnsupportedAudioCodec):
            validation.validate_video(metadata={
                "format": self._format_metadata,
                "streams": [
                    self._video_stream,
                    {
                        "codec_type": "audio",
                        "codec_name": "unknown"
                    }
                ]
            })


    def test_validate_video_invalid_video_codec(self):
        with self.assertRaises(UnsupportedVideoCodec):
            validation.validate_video(metadata={
                "format": self._format_metadata,
                "streams": [
                    self._audio_stream,
                    {
                        "codec_type": "video",
                        "codec_name": "unknown"
                    }
                ]
            })


    def validate_video_missing_video_stream(self):
        with self.assertRaises(MissingVideoStream):
            validation.validate_video(filename=self._filename, metadata={
                "format": self._format_metadata,
                "streams": [self._audio_stream]
            })


    def test_validate_video_without_format_metadata(self):
        with self.assertRaises(InvalidFormatMetadata):
            validation.validate_video(metadata={
                "streams": [self._audio_stream, self._video_stream]
            })


    def test_validate_valid_video(self):
        self.assertTrue(validation.validate_video(metadata=self._metadata))



class TestConversionValidation(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._metadata = get_metadata("tests/resources/ForBiggerBlazes-[codec=h264].mp4")

    def setUp(self) -> None:
        pass

    @staticmethod
    def create_params(container, resolution, vcodec, acodec=None):
        return meta.create_params(container, resolution, vcodec, acodec=acodec)


    def test_container_change(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mov", [1920, 1080], "h264", "mp3" )

        self.assertTrue(validation.validate_transcoding_params(src_params, dst_params, self._metadata))


    def test_video_codec_change(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mp4", [1920, 1080], "h265", "mp3" )

        self.assertTrue(validation.validate_transcoding_params(src_params, dst_params, self._metadata))


    def test_invalid_audio_codec_change(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "aac" )
        with self.assertRaises(validation.UnsupportedAudioCodecConversion):
            validation.validate_transcoding_params(src_params, dst_params, self._metadata)


    def test_resolution_change(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mp4", [640, 360], "h264", "mp3" )

        self.assertTrue(validation.validate_transcoding_params(src_params, dst_params, self._metadata))


    def test_no_audio_codec(self):
        # It is valid to not provide audio codec.
        src_params = self.create_params("mp4", [1920, 1080], "h264", None )
        dst_params = self.create_params("mp4", [640, 360], "h264", None )

        self.assertTrue(validation.validate_transcoding_params(src_params, dst_params, self._metadata))


    def test_invalid_src_video_codec(self):
        src_params = self.create_params("mp4", [1920, 1080], "avi", "mp3" )
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )

        with self.assertRaises(validation.UnsupportedVideoCodec):
            validation.validate_transcoding_params(src_params, dst_params, self._metadata)


    def test_invalid_dst_video_codec(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mp4", [1920, 1080], "avi", "mp3" )

        with self.assertRaises(validation.UnsupportedVideoCodec):
            validation.validate_transcoding_params(src_params, dst_params, self._metadata)


    def test_invalid_resolution_change(self):
        src_params = self.create_params("mp4", [1920, 1080], "h264", "mp3" )
        dst_params = self.create_params("mp4", [1280, 1024], "h264", "mp3" )

        with self.assertRaises(validation.InvalidResolution):
            validation.validate_transcoding_params(src_params, dst_params, self._metadata)

    @parameterized.expand([
        ([333, 333], [333, 333]),
        ([333, 666], [666, 1332]),
        ([1920, 1080], [1366, 768]),
        ([3840, 2160], [2560, 1440]),
    ])
    def test_nonstandard_resolution_change(
            self,
            src_resolution,
            target_resolution,
    ):
        # It is allowed to convert video with non standard resolution
        # to the same resolution.
        src_params = self.create_params("mp4", src_resolution, "h264", "mp3")
        dst_params = self.create_params("mp4", target_resolution, "h264", "mp3")

        self.assertTrue(validation.validate_transcoding_params(src_params, dst_params, self._metadata))

