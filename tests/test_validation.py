import copy
from unittest import TestCase, mock

from parameterized import parameterized

from ffmpeg_tools import codecs
from ffmpeg_tools import exceptions
from ffmpeg_tools import validation
from ffmpeg_tools import formats
from ffmpeg_tools import frame_rate
from ffmpeg_tools import meta
from ffmpeg_tools import utils
from tests.utils import get_absolute_resource_path, make_parameterized_test_name_generator_for_scalar_values


class TestInputValidation(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._filename = get_absolute_resource_path('ForBiggerBlazes-[codec=h264].mp4')
        cls._metadata = meta.get_metadata(cls._filename)
        cls._supported_formats = formats.list_supported_formats()
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
        with self.assertRaises(exceptions.UnsupportedVideoFormat):
            validation.validate_format("jpg")


    def test_validate_target_format_should_accept_muxers(self):
        assert not formats.Container.c_MP4.is_exclusive_demuxer()

        self.assertTrue(validation.validate_target_format(formats.Container.c_MP4.value))


    def test_validate_target_format_should_reject_exclusive_demuxers(self):
        assert formats.Container.c_QUICK_TIME_DEMUXER.is_exclusive_demuxer()

        with self.assertRaises(exceptions.UnsupportedTargetVideoFormat):
            validation.validate_target_format(formats.Container.c_QUICK_TIME_DEMUXER.value)


    def test_validate_valid_video_codecs(self):
        for video_format in self._supported_formats:
            supported_video_codecs = formats.list_supported_video_codecs(video_format)
            for video_codec in supported_video_codecs:
                self.assertTrue(validation.validate_video_codecs(video_codecs=[video_codec], video_format=video_format))


    @mock.patch.object(formats, 'is_supported_video_codec', side_effect=(lambda vformat, codec: codec != 'unknown'))
    def test_validate_invalid_video_codec(self, _mock_is_supported_video_codec):
        with self.assertRaises(exceptions.UnsupportedVideoCodec):
            validation.validate_video_codecs(video_codecs=['h264', 'unknown', 'mjpeg', 'flv1'], video_format="mp4", )


    def test_validate_video_codecs_should_accept_empty_codec_list(self):
        self.assertTrue(validation.validate_video_codecs("mp4", []))


    @mock.patch.object(formats, 'is_supported_video_codec', return_value=True)
    def test_validate_video_codecs_should_reject_missing_codec_name(self, _mock_is_supported_video_codec):
        with self.assertRaises(exceptions.MissingVideoCodec):
            validation.validate_video_codecs("mp4", ['h264', None, 'mjpeg', 'flv1'])


    def test_validate_valid_audio_codecs(self):
        for video_format in self._supported_formats:
            supported_audio_codecs = formats.list_supported_audio_codecs(video_format)
            for audio_codec in supported_audio_codecs:
                self.assertTrue(validation.validate_audio_codecs(audio_codecs=[audio_codec], video_format=video_format))


    @mock.patch.object(formats, 'is_supported_audio_codec', side_effect=(lambda vformat, codec: codec != 'unknown'))
    def test_validate_invalid_audio_codec(self, _mock_is_supported_audio_codec):
        with self.assertRaises(exceptions.UnsupportedAudioCodec):
            validation.validate_audio_codecs(audio_codecs=["unknown", 'ac3', 'mp3'], video_format="mp4")


    def test_validate_audio_codecs_should_accept_empty_codec_list(self):
        self.assertTrue(validation.validate_audio_codecs("mp4", []))


    def test_validate_audio_stream_valid_codecs(self):
        for video_format in self._supported_formats:
            supported_audio_codecs = formats.list_supported_audio_codecs(video_format)
            for audio_codec in supported_audio_codecs:
                self.assertTrue(validation.validate_audio_stream(stream_metadata={"codec_name": "{}".format(audio_codec)},
                                                      video_format=video_format))


    def test_validate_audio_stream_invalid_codec(self):
        with self.assertRaises(exceptions.UnsupportedAudioCodec):
            validation.validate_audio_stream(stream_metadata={"codec_name": "unknown"}, video_format="mp4")


    def test_validate_audio_stream_without_codec(self):
        with self.assertRaises(exceptions.InvalidVideo):
            validation.validate_audio_stream(stream_metadata={}, video_format="mp4")


    def test_validate_video_stream_valid_codecs(self):
        for video_format in self._supported_formats:
            supported_video_codecs = formats.list_supported_video_codecs(video_format)
            for video_codec in supported_video_codecs:
                self.assertTrue(validation.validate_video_stream(stream_metadata={"codec_name": "{}".format(video_codec)},
                                                      video_format=video_format))

    def test_validate_video_stream_invalid_codec(self):
        with self.assertRaises(exceptions.UnsupportedVideoCodec):
            validation.validate_video_stream(stream_metadata={"codec_name": "unknown"}, video_format="mp4")


    def test_validate_video_stream_without_codec(self):
        with self.assertRaises(exceptions.InvalidVideo):
            validation.validate_audio_stream(stream_metadata={}, video_format="mp4")


    def test_validate_video_stream_existence_without_video_stream(self):
        with self.assertRaises(exceptions.MissingVideoStream):
            validation.validate_video_stream_existence(metadata={"streams": [{"codec_type": "audio"}]})


    def test_validate_video_stream_no_streams_key(self):
        with self.assertRaises(exceptions.InvalidVideo):
            validation.validate_video_stream_existence(metadata={})


    def test_validate_video_contains_video_stream(self):
        self.assertTrue(validation.validate_video_stream_existence(metadata={"streams": [{"codec_type": "video"}]}))


    def test_validate_format_metadata_without_missing_format_metadata(self):
        with self.assertRaises(exceptions.InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={})

        with self.assertRaises(exceptions.InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={"format": {}})


    def test_validate_format_metadata_empty_format_names(self):
        with self.assertRaises(exceptions.InvalidFormatMetadata):
            validation.validate_format_metadata(metadata={"format": {"format_name": ""}})


    def test_validate_format_metadata(self):
        self.assertTrue(validation.validate_format_metadata(metadata={"format": self._format_metadata}))


    def test_validate_video_invalid_format(self):
        metadata = dict(self._metadata)
        metadata["format"] = {"format_name": "jpeg"}

        with self.assertRaises(exceptions.UnsupportedVideoFormat):
            validation.validate_video(metadata=metadata)


    def test_validate_video_valid_codecs(self):
        for video_format in self._supported_formats:
            video_codecs = formats.list_supported_video_codecs(video_format)
            audio_codecs = formats.list_supported_audio_codecs(video_format)
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
        with self.assertRaises(exceptions.UnsupportedAudioCodec):
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
        with self.assertRaises(exceptions.UnsupportedVideoCodec):
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


    def test_validate_video_missing_video_stream(self):
        with self.assertRaises(exceptions.MissingVideoStream):
            validation.validate_video(metadata={
                "format": self._format_metadata,
                "streams": [self._audio_stream]
            })


    def test_validate_video_without_format_metadata(self):
        with self.assertRaises(exceptions.InvalidFormatMetadata):
            validation.validate_video(metadata={
                "streams": [self._audio_stream, self._video_stream]
            })


    def test_validate_valid_video(self):
        self.assertTrue(validation.validate_video(metadata=self._metadata))



class TestConversionValidation(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls._metadata = meta.get_metadata(get_absolute_resource_path("ForBiggerBlazes-[codec=h264].mp4"))

    def setUp(self) -> None:
        pass

    @staticmethod
    def create_params(*args, **kwargs):
        return meta.create_params(*args, **kwargs)


    def modify_metadata_with_passed_values(self, container, resolution, vcodec, acodec=None, frame_rate=None):
        metadata = copy.deepcopy(self._metadata)
        metadata['format']['format_name'] = container
        metadata['streams'][0]['width'] = resolution[0]
        metadata['streams'][0]['coded_width'] = resolution[0]
        metadata['streams'][0]['height'] = resolution[1]
        metadata['streams'][0]['coded_height'] = resolution[1]
        metadata['streams'][0]['codec_name'] = vcodec
        metadata['streams'][0]['r_frame_rate'] = frame_rate
        if acodec is not None:
            metadata['streams'][1]['codec_name'] = acodec
        return metadata


    def modify_metadata_for_sample_rate_validation_tests(self, container, video_codec, audio_codec_rate_pairs):
        assert len(audio_codec_rate_pairs) >= 1

        metadata = self.modify_metadata_with_passed_values(container, [640, 480], video_codec, "mp3", 60)
        assert len(metadata['streams']) == 2
        assert metadata['streams'][0]['codec_type'] != 'audio'
        assert metadata['streams'][1]['codec_type'] == 'audio'

        metadata['streams'][1]['codec_name'] = audio_codec_rate_pairs[0][0]
        metadata['streams'][1]['sample_rate'] = audio_codec_rate_pairs[0][1]

        for i, (audio_codec, sample_rate) in enumerate(audio_codec_rate_pairs[1:]):
            metadata['streams'].append({
                'index': i + 2,
                'codec_type': 'audio',
                'codec_name': audio_codec,
                'sample_rate': sample_rate,
                'channels': 1,
            })

        return metadata


    def test_validate_transcoding_params_should_reject_dst_params_without_video_codec(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [640, 480], None, "mp3", 60)

        with self.assertRaises(exceptions.MissingVideoCodec):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})


    @mock.patch.object(formats, 'is_supported_audio_codec', side_effect=(lambda vformat, codec: True))
    def test_target_audio_codec_supports_source_sample_rates(self, _mock_is_supported_audio_codec):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("mp4", "h264", [
            ('aac', 44100),
            ('mp3', 48000),
            ('pcm_u8', 24000),
            ('amr_nb', 8000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264", "mp3", 60)
        dst_audio_encoder_info = {'sample_rates': [48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000]}

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, dst_audio_encoder_info))


    @mock.patch.object(formats, 'is_supported_audio_codec', side_effect=(lambda vformat, codec: True))
    def test_default_target_audio_codec_supports_source_sample_rate(self, _mock_is_supported_audio_codec):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("mp4", "h264", [
            ('aac', 44100),
            ('mp3', 48000),
            ('pcm_u8', 24000),
            ('amr_nb', 8000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264")
        dst_muxer_info = {'default_audio_codec': "mp3"}
        dst_audio_encoder_info = {'sample_rates': [48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000]}

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, dst_audio_encoder_info))


    @mock.patch.object(formats, 'is_supported_audio_codec', side_effect=(lambda vformat, codec: True))
    def test_target_audio_codec_does_not_support_source_sample_rate(self, _mock_is_supported_audio_codec):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("mp4", "h264", [
            ('aac', 44100),
            ('mp3', 48000),
            ('pcm_u8', 5000),
            ('amr_nb', 8000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264", "mp3", 60)
        dst_audio_encoder_info = {'sample_rates': [48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000]}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_transcoding_params(dst_params, metadata, {}, dst_audio_encoder_info)


    @mock.patch.object(formats, 'is_supported_audio_codec', side_effect=(lambda vformat, codec: True))
    def test_default_target_audio_codec_does_not_support_source_sample_rate(self, _mock_is_supported_audio_codec):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("mp4", "h264", [
            ('aac', 44100),
            ('mp3', 48000),
            ('pcm_u8', 5000),
            ('amr_nb', 8000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264")
        dst_muxer_info = {'default_audio_codec': "mp3"}
        dst_audio_encoder_info = {'sample_rates': [48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000]}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, dst_audio_encoder_info))


    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'aac': 'aac'})
    def test_validate_transcoding_params_should_fall_back_to_hardcoded_sample_rates_if_audio_encoder_info_not_available(self):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("webm", "vp8", [
            ('opus', 5000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264", "aac")

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {"aac": utils.SparseRange({5000})}):
            self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, None))

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {"aac": utils.SparseRange({8000})}):
            with self.assertRaises(exceptions.UnsupportedSampleRate):
                validation.validate_transcoding_params(dst_params, metadata, {}, None)


    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'opus': 'libopus'})
    @mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {'libopus': utils.SparseRange({8000})})
    def test_validate_transcoding_params_should_not_validate_sample_rate_if_target_audio_codec_cannot_be_determined(self):
        metadata = self.modify_metadata_for_sample_rate_validation_tests("webm", "vp8", [
            ('opus', 5000),
        ])
        dst_params = self.create_params("mp4", [640, 480], "h264")
        dst_audio_encoder_info = {'sample_rates': [8000]}

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, None, dst_audio_encoder_info))


    def test_container_change(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mov", [1920, 1080], "h264", "mp3", 60)

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))


    def test_container_change_when_target_is_an_exclusive_demuxer(self):
        assert formats.Container.c_MATROSKA_WEBM_DEMUXER.is_exclusive_demuxer()

        metadata = self.modify_metadata_with_passed_values("matroska", [1920, 1080], "h264", "mp3")
        dst_params = self.create_params(formats.Container.c_MATROSKA_WEBM_DEMUXER.value, [1920, 1080], "h264")
        with self.assertRaises(exceptions.UnsupportedTargetVideoFormat):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})


    def test_video_codec_change(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [1920, 1080], "h265", "mp3", 60)

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))


    def test_invalid_audio_codec_change(self):
        assert codecs.AudioCodec.WMAPRO.value not in codecs.AudioCodec.MP3.get_supported_conversions()
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "wmapro", 60)

        with self.assertRaises(exceptions.UnsupportedAudioCodec):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})


    def test_resolution_change(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [640, 360], "h264", "mp3", 60)

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))


    def test_no_audio_codec(self):
        # It is valid to not provide audio codec.
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", None, 60)
        dst_params = self.create_params("mp4", [640, 360], "h264", None, 60)
        dst_muxer_info = {'default_audio_codec': "aac"}

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, {}))


    def test_invalid_src_video_codec(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "avi", "mp3", 60)
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "mp3", 60)

        with self.assertRaises(exceptions.UnsupportedVideoCodec):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})


    def test_invalid_dst_video_codec(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [1920, 1080], "avi", "mp3", 60)

        with self.assertRaises(exceptions.UnsupportedVideoCodec):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})


    def test_invalid_resolution_change(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", 60)
        dst_params = self.create_params("mp4", [1280, 1024], "h264", "mp3", 60)

        with self.assertRaises(exceptions.InvalidResolution):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})

    @parameterized.expand(
        [
            ([333, 333], [333, 333]),
            ([333, 666], [666, 1332]),
            ([1920, 1080], [1366, 768]),
            ([3840, 2160], [2560, 1440]),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['source', 'target']),
    )
    def test_nonstandard_resolution_change(
            self,
            src_resolution,
            target_resolution,
    ):
        # It is allowed to convert video with non standard resolution
        # to the same resolution.
        metadata = self.modify_metadata_with_passed_values("mp4", src_resolution, "h264", "mp3", 60)
        dst_params = self.create_params("mp4", target_resolution, "h264", "mp3", 60)

        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))

    def test_validate_audio_codec_conversion_should_reject_videos_with_more_than_two_channels_if_audio_must_be_transcoded(self):
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "mp3", 60)
        unsupported_metadata = copy.deepcopy(self._metadata)
        unsupported_metadata['streams'][1]['channels'] = validation._MAX_SUPPORTED_AUDIO_CHANNELS + 1
        assert unsupported_metadata['streams'][1]['codec_name'] != "mp3"

        with self.assertRaises(exceptions.UnsupportedAudioChannelLayout):
            validation.validate_transcoding_params(dst_params, unsupported_metadata, {}, {})

    def test_validate_audio_codec_conversion_should_not_reject_videos_with_two_or_less_channels_even_if_audio_must_be_transcoded(self):
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "mp3", 60)
        unsupported_metadata = copy.deepcopy(self._metadata)
        unsupported_metadata['streams'][1]['channels'] = 1
        assert unsupported_metadata['streams'][1]['codec_name'] != "mp3"

        self.assertTrue(validation.validate_transcoding_params(dst_params, unsupported_metadata, {}, {}))

    def test_validate_audio_codec_conversion_should_accept_videos_with_more_than_two_channels_if_audio_does_not_have_to_be_transcoded(self):
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "aac", 60)
        unsupported_metadata = copy.deepcopy(self._metadata)
        unsupported_metadata['streams'][1]['channels'] = validation._MAX_SUPPORTED_AUDIO_CHANNELS + 1
        assert unsupported_metadata['streams'][1]['codec_name'] == "aac"

        self.assertTrue(validation.validate_transcoding_params(dst_params, unsupported_metadata, {}, {}))

    def test_default_audio_codec_should_be_validated_if_dst_audio_codec_missing(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", frame_rate=60)
        dst_params = self.create_params("mp4", [1920, 1080], "h264", acodec=None)
        dst_muxer_info = {'default_audio_codec': "unsupported_audio_codec"}
        with self.assertRaises(exceptions.UnsupportedAudioCodec):
            validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, {})

    def test_default_audio_codec_should_be_ignored_if_dst_audio_codec_present(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3", frame_rate=60)
        dst_params = self.create_params("mp4", [1920, 1080], "h264", acodec="aac")
        dst_muxer_info = {'default_audio_codec': "unsupported_audio_codec"}
        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, {}))

    def test_validation_should_fail_if_ffmpeg_reports_no_default_audio_codec_for_a_format(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "aac", frame_rate=60)
        dst_params = self.create_params("mpeg", [1920, 1080], "mpeg1video")
        dst_muxer_info = {}
        with self.assertRaises(exceptions.UnsupportedAudioCodecConversion):
            validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info, {})

    def test_validation_should_not_fail_even_if_audio_codec_is_not_specified_and_muxer_info_is_not_available(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "aac", frame_rate=60)
        dst_params = self.create_params("mpeg", [1920, 1080], "mpeg1video")
        dst_muxer_info = None
        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, dst_muxer_info))

    @parameterized.expand(
        [
            ('121/2',),
            ('61',),
            ('122',),
            ('100000',),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['rate']),
    )
    def test_source_frame_rate_when_capped_is_validated_as_max_when_implicitly_used_as_target_frame_rate(self, src_frame_rate):
        assert codecs.MAX_SUPPORTED_FRAME_RATE[codecs.VideoCodec.MPEG_1.value] == 60
        assert frame_rate.FrameRate.from_string(src_frame_rate).normalized() not in formats.list_supported_frame_rates()
        assert frame_rate.FrameRate(60) in formats.list_supported_frame_rates()

        metadata = self.modify_metadata_with_passed_values("mov", [1920, 1080], codecs.VideoCodec.MPEG_1.value, "aac", frame_rate=src_frame_rate)
        dst_params = self.create_params("mov", [1920, 1080], codecs.VideoCodec.MPEG_1.value, "aac", frame_rate=None)
        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))

    @parameterized.expand(
        [
            ('121/2',),
            ('61',),
            ('122',),
            ('100000',),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['rate']),
    )
    def test_explicitly_set_target_frame_rate_is_not_capped(self, dst_frame_rate):
        assert codecs.MAX_SUPPORTED_FRAME_RATE[codecs.VideoCodec.MPEG_1.value] == 60
        assert frame_rate.FrameRate.from_string(dst_frame_rate).normalized() not in formats.list_supported_frame_rates()
        assert frame_rate.FrameRate(60) in formats.list_supported_frame_rates()

        metadata = self.modify_metadata_with_passed_values("mov", [1920, 1080], codecs.VideoCodec.MPEG_1.value, "aac", frame_rate=30)
        dst_params = self.create_params("mov", [1920, 1080], codecs.VideoCodec.MPEG_1.value, "aac", frame_rate=dst_frame_rate)
        with self.assertRaises(exceptions.InvalidFrameRate):
            validation.validate_transcoding_params(dst_params, metadata, {}, {})

    def test_source_frame_rate_when_substituted_is_validated_as_the_resulting_value_when_implicitly_used_as_target_frame_rate(self):
        assert frame_rate.FrameRate(25, 2) in codecs.FRAME_RATE_SUBSTITUTIONS.get(codecs.VideoCodec.MPEG_2.value, {})
        assert frame_rate.FrameRate(25, 2) not in formats.list_supported_frame_rates()
        assert frame_rate.FrameRate(12) in formats.list_supported_frame_rates()

        metadata = self.modify_metadata_with_passed_values("mov", [1920, 1080], "mpeg2video", "aac", frame_rate='25/2')
        dst_params = self.create_params("mov", [1920, 1080], "mpeg2video", "aac", frame_rate=None)
        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))

    def test_explicitly_set_target_frame_rate_is_not_substituted(self):
        assert frame_rate.FrameRate(25, 2) in codecs.FRAME_RATE_SUBSTITUTIONS.get(codecs.VideoCodec.MPEG_2.value, {})
        assert frame_rate.FrameRate(25, 2) not in formats.list_supported_frame_rates()
        assert frame_rate.FrameRate(12) in formats.list_supported_frame_rates()

        metadata = self.modify_metadata_with_passed_values("mov", [1920, 1080], "mpeg2video", "aac", frame_rate=30)
        dst_params = self.create_params("mov", [1920, 1080], "mpeg2video", "aac", frame_rate='25/2')
        with self.assertRaises(exceptions.InvalidFrameRate):
            self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))

    def test_target_frame_rate_not_specified(self):
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "aac", frame_rate=60)
        dst_params = self.create_params("mp4", [1920, 1080], "h264", "aac", frame_rate=None)
        self.assertTrue(validation.validate_transcoding_params(dst_params, metadata, {}, {}))

    @parameterized.expand(
        [
            ('-1/-1', None),   # Should use source rate which is malformed
            ('33', None),      # Should use source rate which is unsupported
            (60, 33),          # Should use target rate which is malformed
            (60, '-1/-1'),     # Should use target rate which is unsupported
            (None, None),      # Should use source rate which is missing
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['source', 'target']),
    )
    def test_validate_frame_rate_should_reject_invalid_target_frame_rates(self, src_frame_rate, target_frame_rate):
        dst_params = self.create_params("mp4", [1920, 1080], "h264", frame_rate=target_frame_rate)
        with self.assertRaises(exceptions.InvalidFrameRate):
            validation.validate_frame_rate(dst_params, src_frame_rate)

    @parameterized.expand(
        [
            (60, 30),   # Should use target rate
            (60, None), # Should use source rate
            (None, 60), # Should use target rate and ignore missing source rate
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['source', 'target']),
    )
    def test_validate_frame_rate_should_accept_supported_conversions(self, src_frame_rate, target_frame_rate):
        dst_params = self.create_params("mp4", [1920, 1080], "h264", frame_rate=target_frame_rate)
        self.assertTrue(validation.validate_frame_rate(dst_params, src_frame_rate))

    @parameterized.expand(
        [
            (frame_rate.FrameRate(122), 'h264', frame_rate.FrameRate(122)),
            (frame_rate.FrameRate(60), 'h264', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(122), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(244, 2), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(44, 2), 'mpeg1video', frame_rate.FrameRate(44, 2)),
            (frame_rate.FrameRate(22), 'mpeg1video', frame_rate.FrameRate(22)),
            (frame_rate.FrameRate(60), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(61), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(24, 2), 'mpeg1video', frame_rate.FrameRate(24, 2)),
            (frame_rate.FrameRate(25, 2), 'mpeg1video', frame_rate.FrameRate(25, 2)),
            (frame_rate.FrameRate(24, 2), 'mpeg2video', frame_rate.FrameRate(24, 2)),
            (frame_rate.FrameRate(25, 2), 'mpeg2video', frame_rate.FrameRate(12, 1)),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['source', 'codec', 'target']),
    )
    def test_guess_target_frame_rate(self, src_frame_rate, dst_video_codec, expected_frame_rate):
        dst_params = self.create_params("mp4", [1920, 1080], dst_video_codec, frame_rate=None)
        self.assertEqual(
            validation._guess_target_frame_rate(src_frame_rate, dst_params),
            expected_frame_rate,
        )

    @parameterized.expand(
        [
            (frame_rate.FrameRate(122), 'h264', None),
            (frame_rate.FrameRate(60), 'h264', None),
            (frame_rate.FrameRate(122), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(244, 2), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(44, 2), 'mpeg1video', None),
            (frame_rate.FrameRate(22), 'mpeg1video', None),
            (frame_rate.FrameRate(60), 'mpeg1video', None),
            (frame_rate.FrameRate(61), 'mpeg1video', frame_rate.FrameRate(60)),
            (frame_rate.FrameRate(24, 2), 'mpeg1video', None),
            (frame_rate.FrameRate(25, 2), 'mpeg1video', None),
            (frame_rate.FrameRate(24, 2), 'mpeg2video', None),
            (frame_rate.FrameRate(25, 2), 'mpeg2video', frame_rate.FrameRate(12, 1)),
        ],
        name_func=make_parameterized_test_name_generator_for_scalar_values(['source', 'codec', 'target']),
    )
    def test_guess_target_frame_rate_for_special_cases(self, src_frame_rate, dst_video_codec, expected_value):
        self.assertEqual(
            validation._guess_target_frame_rate_for_special_cases(
                src_frame_rate,
                dst_video_codec
            ),
            expected_value
        )

    def test_get_dst_audio_codec_returns_audio_codec_from_dst_params_if_present(self):
        params = self.create_params("mp4", [333, 333], "h264", acodec="mp3")
        dst_muxer_info = {'default_audio_codec': "aac"}
        self.assertEqual(validation._get_dst_audio_codec(params, dst_muxer_info), 'mp3')

    def test_get_dst_audio_codec_returns_default_audio_codec_if_no_dst_audio_params(self):
        params = self.create_params("mp4", [333, 333], "h264", acodec=None)
        assert 'audio' not in params
        dst_muxer_info = {'default_audio_codec': "aac"}
        self.assertEqual(validation._get_dst_audio_codec(params, dst_muxer_info), 'aac')

    def test_get_dst_audio_codec_returns_default_audio_codec_if_no_codec_in_dst_audio_params(self):
        params = self.create_params("mp4", [333, 333], "h264", audio_bitrate="192k")
        assert 'codec' not in params['audio']
        dst_muxer_info = {'default_audio_codec': "aac"}
        self.assertEqual(validation._get_dst_audio_codec(params, dst_muxer_info), 'aac')

    def test_get_dst_audio_codec_returns_default_audio_codec_if_codec_missing_from_dst_params(self):
        params = self.create_params("mp4", [333, 333], "h264", acodec="mp3")
        params['audio']['codec'] = None
        dst_muxer_info = {'default_audio_codec': "aac"}
        self.assertEqual(validation._get_dst_audio_codec(params, dst_muxer_info), 'aac')

    @mock.patch.dict('ffmpeg_tools.formats._CONTAINER_SUPPORTED_CODECS', {
        "mp4": {'subtitlecodecs': ['subrip', 'ass'], 'videocodecs': ['h264'], 'audiocodecs': 'mp3'},
        "mov": {'subtitlecodecs': ['mov_text'], 'videocodecs': ['h264'], 'audiocodecs': 'mp3'},
    })
    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {
        'subrip': ['subrip', 'mov_text', 'webvtt'],
        'ass':    ['mov_text'],
    })
    def test_validate_transcoding_params_should_accept_subtitles_if_they_can_be_converted_to_anything_supported_by_the_target_format(self):
        dst_params = self.create_params("mov", [1920, 1080], "h264", "mp3", 60)
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3")
        assert meta.count_streams(metadata, codec_type='subtitle') == 0
        assert meta.count_streams(metadata) == 2

        metadata['streams'] += [
            {'index': 2, 'codec_type': 'subtitle', 'codec_name': 'subrip'},
            {'index': 3, 'codec_type': 'subtitle', 'codec_name': 'ass'},
        ]

        self.assertTrue(validation.validate_transcoding_params(
            dst_params,
            metadata,
            dst_muxer_info={},
            dst_audio_encoder_info={},
            strip_unsupported_data_streams=False,
            strip_unsupported_subtitle_streams=False,
        ))

    @mock.patch.dict('ffmpeg_tools.formats._CONTAINER_SUPPORTED_CODECS', {
        "mp4": {'subtitlecodecs': ['subrip', 'ass'], 'videocodecs': ['h264'], 'audiocodecs': 'mp3'},
        "mov": {'subtitlecodecs': ['mov_text'], 'videocodecs': ['h264'], 'audiocodecs': 'mp3'},
    })
    @mock.patch.dict('ffmpeg_tools.codecs._SUBTITLE_SUPPORTED_CONVERSIONS', {
        'subrip': ['subrip', 'mov_text', 'webvtt'],
        'ass':    [],
    })
    def test_validate_transcoding_params_should_reject_unstripped_subtitles_if_they_cannot_be_converted_to_anything_supported_by_the_target_format(self):
        dst_params = self.create_params("mov", [1920, 1080], "h264", "mp3", 60)
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3")
        assert meta.count_streams(metadata, codec_type='subtitle') == 0
        assert meta.count_streams(metadata) == 2

        metadata['streams'] += [
            {'index': 2, 'codec_type': 'subtitle', 'codec_name': 'subrip'},
            {'index': 3, 'codec_type': 'subtitle', 'codec_name': 'ass'},
        ]

        with self.assertRaises(exceptions.UnsupportedSubtitleCodecConversion):
            validation.validate_transcoding_params(
                dst_params,
                metadata,
                dst_muxer_info={},
                dst_audio_encoder_info={},
                strip_unsupported_data_streams=False,
                strip_unsupported_subtitle_streams=False,
            )

    def test_validate_transcoding_params_should_gracefully_handle_subtitle_codecs_not_in_the_subtitle_codec_enum(self):
        assert 'undefined codec' not in codecs.SubtitleCodec._value2member_map_

        dst_params = self.create_params("mov", [1920, 1080], "h264", "mp3", 60)
        metadata = self.modify_metadata_with_passed_values("mp4", [1920, 1080], "h264", "mp3")
        assert meta.count_streams(metadata, codec_type='subtitle') == 0
        assert meta.count_streams(metadata) == 2

        metadata['streams'] += [
            {'index': 2, 'codec_type': 'subtitle', 'codec_name': 'undefined codec'},
        ]

        with self.assertRaises(exceptions.UnsupportedSubtitleCodecConversion):
            validation.validate_transcoding_params(
                dst_params,
                metadata,
                dst_muxer_info={},
                dst_audio_encoder_info={},
                strip_unsupported_data_streams=False,
                strip_unsupported_subtitle_streams=False,
            )


class TestValidateUnsupportedStreams(TestCase):
    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_data_streams', return_value=[2, 3, 5])
    def test_validate_unsupported_data_streams_raises_exception_if_unsupported_data_streams_cant_be_stripped(
        self,
        _mock_find_unsupported_data_streams,
    ):
        with self.assertRaises(exceptions.UnsupportedStream):
            validation.validate_unsupported_data_streams(
                metadata={},
                strip_unsupported_data_streams=False,
            )

    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_data_streams', return_value=[2, 3, 5])
    def test_validate_unsupported_data_streams_does_not_raise_if_unsupported_data_streams_can_be_stripped(
        self,
        _mock_find_unsupported_data_streams,
    ):
        self.assertTrue(validation.validate_unsupported_data_streams(
            metadata={},
            strip_unsupported_data_streams=True,
        ))

    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_data_streams', return_value=[])
    def test_validate_unsupported_data_streams_does_not_raise_if_no_unsupported_data_streams(
        self,
        _mock_find_unsupported_data_streams,
    ):
        self.assertTrue(validation.validate_unsupported_data_streams(
            metadata={},
            strip_unsupported_data_streams=False,
        ))

    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_subtitle_streams', return_value=[2, 3, 5])
    def test_validate_unsupported_subtitle_streams_raises_exception_if_unsupported_subtitle_streams_cant_be_stripped(
        self,
        _mock_find_unsupported_subtitle_streams,
    ):
        with self.assertRaises(exceptions.UnsupportedSubtitleCodecConversion):
            validation.validate_unsupported_subtitle_streams(
                metadata={},
                strip_unsupported_subtitle_streams=False,
                target_container=formats.Container.c_MATROSKA,
            )

    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_subtitle_streams', return_value=[2, 3, 5])
    def test_validate_unsupported_subtitle_streams_does_not_raise_if_unsupported_subtitle_streams_can_be_stripped(
        self,
        _mock_find_unsupported_subtitle_streams,
    ):
        self.assertTrue(validation.validate_unsupported_subtitle_streams(
            metadata={},
            strip_unsupported_subtitle_streams=True,
            target_container=formats.Container.c_MATROSKA,
        ))

    @mock.patch('ffmpeg_tools.validation.commands.find_unsupported_subtitle_streams', return_value=[])
    def test_validate_unsupported_subtitle_streams_does_not_raise_if_no_unsupported_subtitle_streams(
        self,
        _mock_find_unsupported_subtitle_streams,
    ):
        self.assertTrue(validation.validate_unsupported_subtitle_streams(
            metadata={},
            strip_unsupported_subtitle_streams=False,
            target_container=formats.Container.c_MATROSKA,
        ))

    def test_validate_unsupported_subtitle_streams_needs_a_known_target_container(self):
        with self.assertRaises(exceptions.InvalidVideo):
            validation.validate_unsupported_subtitle_streams(
                metadata={},
                strip_unsupported_subtitle_streams=False,
                target_container=None,
            )


class TestValidateAudioSampleRates(TestCase):

    def test_should_allow_rates_supported_by_encoder_if_codec_does_not_change(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 44100},
            {'index': 1, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 48000},
            {'index': 2, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 8000},
        ]}
        dst_encoder_info = {'sample_rates': {48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000}}

        self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info))

    def test_should_allow_rates_supported_by_encoder_if_codec_changes(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': 44100},
            {'index': 1, 'codec_type': 'audio', 'codec_name': 'amr_nb', 'sample_rate': 48000},
            {'index': 2, 'codec_type': 'audio', 'codec_name': 'pcm_u8', 'sample_rate': 8000},
        ]}
        dst_encoder_info = {'sample_rates': {48000, 44100, 32000, 24000, 22050, 16000, 12000, 11025, 8000}}

        self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info))

    def test_should_not_allow_rates_unsupported_by_encoder_if_codec_does_not_change(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 44100},
            {'index': 1, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 48000},
            {'index': 2, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 8000},
        ]}
        dst_encoder_info = {'sample_rates': {48000}}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info)

    def test_should_not_allow_rates_unsupported_by_encoder_if_codec_changes(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'aac', 'sample_rate': 44100},
            {'index': 1, 'codec_type': 'audio', 'codec_name': 'amr_nb', 'sample_rate': 48000},
            {'index': 2, 'codec_type': 'audio', 'codec_name': 'pcm_u8', 'sample_rate': 8000},
        ]}
        dst_encoder_info = {'sample_rates': {48000}}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info)

    def test_should_allow_videos_with_no_audio(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'video', 'codec_name': 'h264'},
            {'index': 1, 'codec_type': 'subtitle', 'codec_name': 'subrip'},
        ]}
        dst_encoder_info = {'sample_rates': {48000}}

        self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info))
        self.assertTrue(validation.validate_audio_sample_rates({'streams': []}, 'mp3', dst_encoder_info))
        self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', {'sample_rates': {}}))

    def test_should_not_allow_anything_if_encoder_supports_no_sample_rates(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 44100},
        ]}
        dst_encoder_info = {'sample_rates': {}}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info)

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'mp3': 'libmp3lame'})
    def test_should_fall_back_to_hardcoded_rates_if_encoder_does_not_provide_information_about_sample_rates(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 44100},
        ]}

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {'libmp3lame': utils.SparseRange({44100})}):
            self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', {}))

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {'libmp3lame': utils.SparseRange(set())}):
            with self.assertRaises(exceptions.UnsupportedSampleRate):
                validation.validate_audio_sample_rates(metadata, 'mp3', {})

    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'mp3': 'libmp3lame'})
    def test_should_fall_back_to_hardcoded_rates_if_encoder_info_is_not_available_at_all(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'mp3', 'sample_rate': 44100},
        ]}

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {'libmp3lame': utils.SparseRange({44100})}):
            self.assertTrue(validation.validate_audio_sample_rates(metadata, 'mp3', None))

        with mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {'libmp3lame': utils.SparseRange(set())}):
            with self.assertRaises(exceptions.UnsupportedSampleRate):
                validation.validate_audio_sample_rates(metadata, 'mp3', None)

    def test_should_not_allow_files_with_unknown_sample_rate(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'aac'},
        ]}
        dst_encoder_info = {'sample_rates': {48000}}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_audio_sample_rates(metadata, 'mp3', dst_encoder_info)

    @mock.patch.dict('ffmpeg_tools.codecs._SUPPORTED_SAMPLE_RATES', {})
    @mock.patch.dict('ffmpeg_tools.codecs._AUDIO_ENCODERS', {'aac': 'aac'})
    def test_should_not_allow_files_with_unknown_sample_rate_even_if_supported_sample_rates_cannot_be_determined(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'audio', 'codec_name': 'aac'},
        ]}

        with self.assertRaises(exceptions.UnsupportedSampleRate):
            validation.validate_audio_sample_rates(metadata, 'mp3', None)

    def test_should_not_confuse_audio_with_other_types_of_streams(self):
        metadata = {'streams': [
            {'index': 0, 'codec_type': 'video', 'codec_name': 'aac', 'sample_rate': 44100},
            {'index': 1, 'codec_type': 'subtitle', 'codec_name': 'aac', 'sample_rate': 48000},
            {'index': 2, 'codec_type': 'data', 'codec_name': 'aac', 'sample_rate': 8000},
            {'index': 3, 'codec_name': 'aac', 'sample_rate': 8000},
        ]}
        dst_encoder_info = {'aac': {22000}}

        self.assertTrue(validation.validate_audio_sample_rates(metadata, 'aac', dst_encoder_info))
