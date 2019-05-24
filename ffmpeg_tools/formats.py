import enum

from . import validation
from . import codecs



class Container(enum.Enum):
    # The values below are **muxer** names, which means that they can be passed
    # to ffmpeg using the -f option to specify the target format.
    c_3G2 = "3g2"           # 3GP2 (3GPP2 file format) muxer
    c_3GP = "3gp"           # 3GP (3GPP file format) muxer
    c_AVI = "avi"           # AVI (Audio Video Interleaved) muxer
    c_F4V = "f4v"           # F4V Adobe Flash Video muxer
    c_MATROSKA = "matroska" # Matroska; .mkv extension muxer
    c_MP4 = "mp4"           # MP4 (MPEG-4 Part 14) muxer
    c_MPEG = "mpeg"         # MPEG-1 Systems / MPEG program stream muxer
    c_MOV = "mov"           # QuickTime / MOV muxer
    c_WEBM = "webm"         # WebM muxer

    # Unfortunately ffprobe can't read muxer name back from an existing container.
    # what it gives us instead is a **demuxer** name. In many cases those names
    # are the same but there are significant exceptions. The values below are
    # those exceptions. We need them to be able to validate the format of an
    # input file but they won't work when used as tgarget formats.
    #
    # Note that while these names may simply look like a list of
    # muxer names, they're not reliable that way. For example 'mov,mp4,m4a,3gp,3g2,mj2'
    # covers also files created by the 'f4v' muxer. And `mpegts' is both a
    # muxer and demuxer but the demuxer handles also files created by the 'svcd' muxer.
    c_QUICK_TIME_DEMUXER = "mov,mp4,m4a,3gp,3g2,mj2" # QuickTime / MOV
    c_MATROSKA_WEBM_DEMUXER = "matroska,webm"        # Matroska / WebM


    # Normally enum throws ValueError, when initialization value is invalid.
    # We want to return more meaningful exception. This function is called by
    # enum when all conversion options failed.
    @classmethod
    def _missing_(cls, value):
        raise validation.UnsupportedVideoFormat(value)

    @staticmethod
    def from_name(name: str) -> 'Container':
        return Container(name.lower())

    def get_supported_video_codecs(self):
        if self.value not in _CONTAINER_SUPPORTED_CODECS:
            return []

        return _CONTAINER_SUPPORTED_CODECS[self.value]["videocodecs"]

    def get_supported_audio_codecs(self):
        if self.value not in _CONTAINER_SUPPORTED_CODECS:
            return []

        return _CONTAINER_SUPPORTED_CODECS[self.value]["audiocodecs"]

    def is_supported_video_codec(self, vcodec):
        if isinstance(vcodec, codecs.VideoCodec):
            return vcodec.value in self.get_supported_video_codecs()
        elif isinstance(vcodec, str):
            return vcodec in self.get_supported_video_codecs()

    def is_supported_audio_codec(self, acodec):
        if isinstance(acodec, codecs.AudioCodec):
            return acodec.value in self.get_supported_audio_codecs()
        elif isinstance(acodec, str):
            return acodec in self.get_supported_audio_codecs()

    @staticmethod
    def is_supported(vformat):
        return vformat in list_supported_formats()

    @staticmethod
    def list_supported_formats(vformat):
        return list_supported_formats()


_MOV_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "HEVC",
        "mpeg1video",
        "mpeg2video",

    ],
    "audiocodecs": [
        "mp3",
        "aac",
    ]
}

_MP4_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "HEVC",
    ],
    "audiocodecs": [
        "aac",
        "mp3",
    ]
}

_MKV_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "HEVC",
        "mpeg1video",
        "mpeg2video",
    ],
    "audiocodecs": [
        "mp3",
        "aac",
    ]
}

_WEBM_CODECS = {
    "videocodecs": [
        "vp8",
        "vp9",
    ],
    "audiocodecs": [
        "opus",
    ]
}

_AVI_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "HEVC",
        "mpeg1video",
        "mpeg2video",
    ],
    "audiocodecs": [
        "opus",
    ]
}

_3GP_CODECS = {
    "videocodecs": [
        "h264",
    ],
    "audiocodecs": [
        "aac",
    ]
}

_MPEG_CODECS = {
    "videocodecs": [
        "mpeg1video",
        "mpeg2video",
    ],
    "audiocodecs": [
        "mp3",
    ]
}

_QUICKTIME_CODECS = {
    "videocodecs": list(set(
        _MOV_CODECS["videocodecs"] +
        _MP4_CODECS["videocodecs"] +
        _3GP_CODECS["videocodecs"]
    )),
    "audiocodecs": list(set(
        _MOV_CODECS["audiocodecs"] +
        _MP4_CODECS["audiocodecs"] +
        _3GP_CODECS["audiocodecs"]
    )),
}

_MATROSKA_WEBM_CODECS = {
    "videocodecs": list(set(_MKV_CODECS["videocodecs"] + _WEBM_CODECS["videocodecs"])),
    "audiocodecs": list(set(_MKV_CODECS["audiocodecs"] + _WEBM_CODECS["audiocodecs"])),
}


_CONTAINER_SUPPORTED_CODECS = {
    "3g2": _3GP_CODECS,
    "3gp": _3GP_CODECS,
    "avi": _AVI_CODECS,
    "matroska": _MKV_CODECS,
    "matroska,webm": _MATROSKA_WEBM_CODECS,
    "mov": _MOV_CODECS,
    "mp4": _MP4_CODECS,
    "mov,mp4,m4a,3gp,3g2,mj2": _QUICKTIME_CODECS,
    "mpeg": _MPEG_CODECS,
    "webm": _WEBM_CODECS,
}

_resolutions = {
    "16:9": [
        [640, 260],
        [1280, 720],
        [1536, 864],
        [1920, 1080],
        [2048, 1152],
        [2560, 1440],
        [3840, 2160],
        [1366, 768],
        [1360, 768]
    ],
    "4:3": [
        [800, 600],
        [1024, 768]
    ],
    "16:10": [
        [1280, 800],
        [1440, 900],
        [1680, 1050],
        [1920, 1200]
    ],
    "5:4": [
        [1280, 1024]
    ],
    "21:9": [
        [2560, 1080],
        [3440, 1440]
    ]
}


def list_supported_formats():
    return [c.value for c in Container]


def is_supported(vformat):
    return Container.is_supported(vformat)


def list_supported_video_codecs(vformat):
    if vformat not in Container._value2member_map_:
        return []

    return Container(vformat).get_supported_video_codecs()


def is_supported_video_codec(vformat, codec):
    return codec in list_supported_video_codecs(vformat)


def list_supported_audio_codecs(vformat):
    if vformat not in Container._value2member_map_:
        return []

    return Container(vformat).get_supported_audio_codecs()


def is_supported_audio_codec(vformat, codec):
    return codec in list_supported_audio_codecs(vformat)


def list_matching_resolutions(resolution):
    for aspect, resolutions_list in _resolutions.items():
        if resolution in resolutions_list:
            return resolutions_list
    return [resolution]

