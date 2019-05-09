import sys
import pytest

import ffmpeg_tools as ffmpeg


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
                "timed_thumbnails": 0
            }
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
                "timed_thumbnails": 0
            }
        }
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
            "encoder": "Lavf57.66.105"
        }
    }
}



class TestMetadata(object):

    def test_getting_resolution(self):
        assert(ffmpeg.meta.get_resolution(example_metadata) == [1920, 1080])

    def test_get_duration(self):
        assert(ffmpeg.meta.get_duration(example_metadata) == 46.120000 )

    def test_get_video_codec(self):
        assert(ffmpeg.meta.get_video_codec(example_metadata) == "vp9" )

    def test_get_audio_codec(self):
        assert(ffmpeg.meta.get_audio_codec(example_metadata) == "opus" )

    def test_get_format(self):
        assert(ffmpeg.meta.get_format(example_metadata) == "matroska,webm" )

