import enum
from typing import List, Optional

from . import exceptions
from . import frame_rate


DATA_STREAM_WHITELIST = [
    'bin_data'
]


SUBTITLE_STREAM_WHITELIST = [
    'subrip'
]


class VideoCodec(enum.Enum):
    AV1 = "av1"              # Alliance for Open Media AV1
    FLV1 = "flv1"            # FLV / Sorenson Spark / Sorenson H.263 (Flash Video)
    H_263 = "h263"           # H.263 / H.263-1996,
                             # H.263+ / H.263-1998 / H.263 version 2
    H_264 = "h264"           # H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10
    H_265 = "h265"
    HEVC = "hevc"            # H.265 / HEVC (High Efficiency Video Coding)
    MJPEG = "mjpeg"          # Motion JPEG
    MPEG_1 = "mpeg1video"    # MPEG-1 video
    MPEG_2 = "mpeg2video"    # MPEG-2 video
    MPEG_4 = "mpeg4"         # MPEG-4 part 2
    MSMPEG4V2 = "msmpeg4v2"  # MPEG-4 part 2 Microsoft variant version 2
    THEORA = "theora"        # Theora
    VP8 = "vp8"              # On2 VP8
    VP9 = "vp9"              # Google VP9
    WMV1 = "wmv1"            # Windows Media Video 7
    WMV2 = "wmv2"            # Windows Media Video 8
    WMV3 = "wmv3"            # Windows Media Video 9


    # Normally enum throws ValueError, when initialization value is invalid.
    # We want to return more meaningful exception. This function is called by
    # enum when all conversion options failed.
    @classmethod
    def _missing_(cls, value):
        raise exceptions.UnsupportedVideoCodec(value, "")

    @staticmethod
    def from_name(name: str) -> 'VideoCodec':
        return VideoCodec(name)

    # FFMPEG needs encoder name, instead of codec name as transcoding parameter.
    # If list doesn't contain encoder we assume that we can pass codec name.
    def get_encoder(self) -> Optional[str]:
        return _VIDEO_ENCODERS.get(self.value, self.value)

    def get_supported_conversions(self) -> List[str]:
        return _VIDEO_SUPPORTED_CONVERSIONS.get(self.value, [])

    def can_convert(self, video_codec: str) -> bool:
        return video_codec in self.get_supported_conversions()


class AudioCodec(enum.Enum):
    AAC = "aac"        # AAC (Advanced Audio Coding)
    AC3 = "ac3"        # ATSC A/52A (AC-3)
    AMR_NB = "amr_nb"  # AMR-NB (Adaptive Multi-Rate NarrowBand)
    MP2 = "mp2"        # MP2 (MPEG audio layer 2)
    MP3 = "mp3"        # MP3 (MPEG audio layer 3)
    OPUS = "opus"      # Opus (Opus Interactive Audio Codec)
    PCM_U8 = "pcm_u8"  # PCM unsigned 8-bit
    WMAV2 = "wmav2"    # Windows Media Audio 2
    WMAPRO = "wmapro"  # Windows Media Audio 9 Professional
    VORBIS = "vorbis"  # Vorbis


    # Normally enum throws ValueError, when initialization value is invalid.
    # We want to return more meaningful exception. This function is called by
    # enum when all conversion options failed.
    @classmethod
    def _missing_(cls, value):
        raise exceptions.UnsupportedAudioCodec(value, "")

    @staticmethod
    def from_name(name: str) -> 'AudioCodec':
        return AudioCodec(name)

    # FFMPEG needs encoder name, instead of codec name as transcoding parameter.
    # If list doesn't contain encoder we assume that we can pass codec name.
    def get_encoder(self) -> Optional[str]:
        return _AUDIO_ENCODERS.get(self.value, self.value)

    def get_supported_conversions(self) -> List[str]:
        return _AUDIO_SUPPORTED_CONVERSIONS.get(self.value, [])

    def can_convert(self, audio_codec: str) -> bool:
        return audio_codec in self.get_supported_conversions()


_VIDEO_ENCODERS = {
    "av1": None,                    # libaom-av1 is still experimental
    "flv1": "flv",
    "h263": "h263",
    "h264": "libx264",
    "h265": "libx265",
    "hevc": "libx265",
    "mjpeg": "mjpeg",               # Alternatives: mjpeg_vaapi
    "mpeg1video": "mpeg1video",
    "mpeg2video": "mpeg2video",
    "mpeg4": "libxvid",
    "msmpeg4v2": "msmpeg4v2",
    "theora": "libtheora",
    "vp8": "libvpx",                # Alternatives: vp8_vaapi, vp8_v4l2m2m
    "vp9": "libvpx-vp9",            # Alternatives: vp9_vaapi
    "wmv1": "wmv1",
    "wmv2": "wmv2",
    "wmv3": None,
}

_AUDIO_ENCODERS = {
    "aac": "aac",
    "ac3": "ac3",
    "amr_nb": "libopencore_amrnb",
    "mp2": "mp2",                   # Alternatives: mp2fixed
    "mp3": "libmp3lame",
    "opus": "libopus",
    "pcm_u8": "pcm_u8",
    "wmapro": None,
    "wmav2": "wmav2",
    "vorbis": "libvorbis",
}


_VIDEO_SUPPORTED_CONVERSIONS = {
    #              "av1", "flv1", "h263", "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4", "msmpeg4v2", "theora", "vp8", "vp9", "wmv1", "wmv2", "wmv3"
    "av1":        [                                                                                                                                                        ],
    "flv1":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "h263":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "h264":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "h265":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "hevc":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "mjpeg":      [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "mpeg1video": [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "mpeg2video": [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "mpeg4":      [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "msmpeg4v2":  [                                                                                                                                                        ],
    "theora":     [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "vp8":        [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "vp9":        [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "wmv1":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "wmv2":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
    "wmv3":       [       "flv1",         "h264", "h265", "hevc", "mjpeg", "mpeg1video", "mpeg2video", "mpeg4",                        "vp8", "vp9", "wmv1", "wmv2"        ],
}

_AUDIO_SUPPORTED_CONVERSIONS = {
    #          "aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8", "wmapro", "wmav2", "vorbis"
    "aac":    ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "ac3":    ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "amr_nb": ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "mp2":    ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "mp3":    ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "opus":   ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "pcm_u8": ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "wmapro": ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "wmav2":  ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
    "vorbis": ["aac", "ac3", "amr_nb", "mp2", "mp3", "opus", "pcm_u8",           "wmav2", "vorbis"],
}

_PRESERVE_QUALITY_COMMAND = {
    "h264" : [ "-crf", "22" ],
    "h265" : [ "-crf", "22" ],
    "vp8" : [ "-crf", "22", "-b:v", "0" ],
    "vp9" : [ "-crf", "22", "-b:v", "0" ]
}


def get_video_encoder(target_codec: str) -> Optional[str]:
    # This will throw exception for unsupported codecs.
    codec = VideoCodec(target_codec)
    return codec.get_encoder()


def preserve_quality_command(target_codec: str) -> List[str]:
    # TODO: Hack function to preserve video quality for some formats.
    # Create better and more generic solution in future.
    return _PRESERVE_QUALITY_COMMAND.get(target_codec, [])


def get_audio_encoder(target_codec: str) -> Optional[str]:
    # This will throw exception for unsupported codecs.
    codec = AudioCodec(target_codec)
    return codec.get_encoder()


def list_supported_video_conversions(codec: str) -> List[str]:
    if codec not in VideoCodec._value2member_map_:
        return []

    return VideoCodec(codec).get_supported_conversions()


def list_supported_audio_conversions(codec: str) -> List[str]:
    if codec not in AudioCodec._value2member_map_:
        return []

    return AudioCodec(codec).get_supported_conversions()


MAX_SUPPORTED_FRAME_RATE = {
    VideoCodec.MPEG_1.value: 60
}

FRAME_RATE_SUBSTITUTIONS = {
    VideoCodec.MPEG_2.value: {
        frame_rate.FrameRate(25, 2): frame_rate.FrameRate(12),
    }
}
assert all(
    original == original.normalized() and substitute == substitute.normalized()
    for codec, rules in FRAME_RATE_SUBSTITUTIONS.items()
    for original, substitute in rules.items()
)
