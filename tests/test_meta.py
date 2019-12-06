from unittest import TestCase, mock

from ffmpeg_tools import meta


example_metadata = {
    "streams": [
        {
            "index": 0,
            "codec_name": "vp9",
            "codec_long_name": "Google VP9",
            "profile": "Profile 0",
            "codec_type": "video",
            "codec_time_base": "1/25",
            "codec_tag_string": "[0][0][0][0]",
            "codec_tag": "0x0000",
            "width": 1920,
            "height": 1080,
            "coded_width": 1920,
            "coded_height": 1080,
            "has_b_frames": 0,
            "sample_aspect_ratio": "1:1",
            "display_aspect_ratio": "16:9",
            "pix_fmt": "yuv420p",
            "level": -99,
            "color_range": "tv",
            "chroma_location": "left",
            "refs": 1,
            "r_frame_rate": "25/1",
            "avg_frame_rate": "25/1",
            "time_base": "1/1000",
            "start_pts": 7,
            "start_time": "0.007000",
            "disposition": {
                "default": 1,
                "dub": 0,
                "original": 0,
                "comment": 0,
                "lyrics": 0,
                "karaoke": 0,
                "forced": 0,
                "hearing_impaired": 0,
                "visual_impaired": 0,
                "clean_effects": 0,
                "attached_pic": 0,
                "timed_thumbnails": 0,
            },
        },
        {
            "index": 1,
            "codec_name": "opus",
            "codec_long_name": "Opus (Opus Interactive Audio Codec)",
            "codec_type": "audio",
            "codec_time_base": "1/48000",
            "codec_tag_string": "[0][0][0][0]",
            "codec_tag": "0x0000",
            "sample_fmt": "fltp",
            "sample_rate": "48000",
            "channels": 2,
            "channel_layout": "stereo",
            "bits_per_sample": 0,
            "r_frame_rate": "0/0",
            "avg_frame_rate": "0/0",
            "time_base": "1/1000",
            "start_pts": -7,
            "start_time": "-0.007000",
            "disposition": {
                "default": 1,
                "dub": 0,
                "original": 0,
                "comment": 0,
                "lyrics": 0,
                "karaoke": 0,
                "forced": 0,
                "hearing_impaired": 0,
                "visual_impaired": 0,
                "clean_effects": 0,
                "attached_pic": 0,
                "timed_thumbnails": 0,
            },
        },
    ],
    "format": {
        "filename": "/home/nieznanysprawiciel/Data/Transcoding/different-codecs/Panasonic-[codec=vp9].webm",
        "nb_streams": 2,
        "nb_programs": 0,
        "format_name": "matroska,webm",
        "format_long_name": "Matroska / WebM",
        "start_time": "-0.007000",
        "duration": "46.120000",
        "size": "2246711",
        "bit_rate": "389715",
        "probe_score": 100,
        "tags": {
            "encoder": "Lavf57.66.105",
        },
    },
}



class TestMetadata(TestCase):

    def test_getting_resolution(self):
        self.assertEqual(meta.get_resolution(example_metadata), [1920, 1080])

    def test_get_duration(self):
        self.assertEqual(meta.get_duration(example_metadata), 46.120000)

    def test_get_video_codec(self):
        self.assertEqual(meta.get_video_codec(example_metadata), "vp9")

    def test_get_audio_codec(self):
        self.assertEqual(meta.get_audio_codec(example_metadata), "opus")

    def test_get_format(self):
        self.assertEqual(meta.get_format(example_metadata), "matroska,webm")

    def test_get_audio_stream(self):
        self.assertEqual(meta.get_audio_stream(example_metadata), example_metadata['streams'][1])

    def test_get_metadata_invalid_path(self):
        self.assertEqual(meta.get_metadata("blabla"), {})

    def test_count_streams(self):
        metadata = {'streams': [
            {"codec_type": "video"},
            {"codec_type": "audio"},
            {"codec_type": "audio"},
            {"codec_type": "subtitle"},
            {"codec_type": "data"},
            {"codec_type": "whatever"},
            {"codec_type": ""},
            {"codec_type": None},
            {},
        ]}
        self.assertEqual(meta.count_streams(metadata), 9)
        self.assertEqual(meta.count_streams(metadata, codec_type=None), 9)
        self.assertEqual(meta.count_streams(metadata, codec_type='video'), 1)
        self.assertEqual(meta.count_streams(metadata, codec_type='audio'), 2)
        self.assertEqual(meta.count_streams(metadata, codec_type='subtitle'), 1)
        self.assertEqual(meta.count_streams(metadata, codec_type='data'), 1)
        self.assertEqual(meta.count_streams(metadata, codec_type='whatever'), 1)
        self.assertEqual(meta.count_streams(metadata, codec_type='nothing'), 0)
        self.assertEqual(meta.count_streams(metadata, codec_type=''), 1)

    def test_find_stream_indexes(self):
        metadata = {'streams': [
            {"codec_type": "video", 'index': 0},
            {"codec_type": "audio", 'index': 1},
            {"codec_type": "audio", 'index': 2},
            {"codec_type": "subtitle", 'index': 3},
            {"codec_type": "subtitle", 'index': 3},
            {"codec_type": "data", 'index': 4},
            {"codec_type": "whatever", 'index': 5},
            {"codec_type": "", 'index': 6},
            {"codec_type": None, 'index': 7},
            {'index': 8},
            {"codec_type": "audio", 'index': '2'},
            {"codec_type": "audio", 'index': {}},
            {"codec_type": "video", 'index': None},
            {"codec_type": "subtitle"},
            {},
        ]}
        self.assertCountEqual(meta.find_stream_indexes(metadata), [0, 1, 2, 3, 3, 4, 5, 6, 7, 8, '2', {}, None, None, None])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='video'), [0, None])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='audio'), [1, 2, '2', {}])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='subtitle'), [3, 3, None])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='data'), [4])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='whatever'), [5])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type='nothing'), [])
        self.assertCountEqual(meta.find_stream_indexes(metadata, codec_type=''), [6])

    def test_get_attribute_from_all_streams(self):
        metadata = {'streams': [
            {"codec_type": "video", 'index': 0},
            {"codec_type": "audio", 'index': 1},
            {"codec_type": "audio", 'index': 2},
            {"codec_type": "subtitle", 'index': 3},
            {"codec_type": "data", 'index': 4},
            {"codec_type": "whatever", 'index': 5},
            {"codec_type": "", 'index': 6},
            {"codec_type": None, 'index': 7},
            {'index': 8},
        ]}
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index'), range(9))
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type=None), range(9))
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='video'), [0])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='audio'), [1, 2])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='subtitle'), [3])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='data'), [4])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='whatever'), [5])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='nothing'), [])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type=''), [6])

    def test_get_attribute_from_all_streams_should_support_duplicates(self):
        metadata = {'streams': [
            {"codec_type": "audio", 'index': 2},
            {"codec_type": "subtitle", 'index': 2},
            {"codec_type": "subtitle", 'index': 2},
        ]}
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index'), [2, 2, 2])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='video'), [])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='audio'), [2])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='subtitle'), [2, 2])

    def test_get_attribute_from_all_streams_should_support_non_integer_values(self):
        metadata = {'streams': [
            {"codec_type": "audio", 'index': '2'},
            {"codec_type": "subtitle", 'index': {}},
            {"codec_type": "subtitle", 'index': None},
        ]}
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index'), ['2', {}, None])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='video'), [])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='audio'), ['2'])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='subtitle'), [{}, None])

    def test_get_attribute_from_all_streams_should_support_missing_values(self):
        metadata = {'streams': [
            {"codec_type": "subtitle", 'index': 0},
            {"codec_type": "subtitle", 'index': None},
            {"codec_type": "subtitle"},
            {},
        ]}
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index'), [0, None, None, None])
        self.assertCountEqual(meta.get_attribute_from_all_streams(metadata, 'index', codec_type='subtitle'), [0, None, None])
