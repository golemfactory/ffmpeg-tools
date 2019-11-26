import enum
from math import gcd
from typing import List, NamedTuple, Union, Set

from . import codecs
from . import exceptions
from . import frame_rate



class Container(enum.Enum):
    # The values below are **muxer** names, which means that they can be passed
    # to ffmpeg using the -f option to specify the target format.
    c_3G2 = "3g2"           # 3GP2 (3GPP2 file format) muxer
    c_3GP = "3gp"           # 3GP (3GPP file format) muxer
    c_ASF = "asf"           # ASF (Advanced / Active Streaming Format) muxer; .asf and .wmv extensions
    c_AVI = "avi"           # AVI (Audio Video Interleaved) muxer
    c_F4V = "f4v"           # F4V Adobe Flash Video muxer
    c_FLV = "flv"           # FLV (Flash Video) muxer
    c_IPOD = "ipod"         # iPod H.264 MP4 (MPEG-4 Part 14) muxer; .m4v extension
    c_MATROSKA = "matroska" # Matroska; .mkv extension muxer
    c_MOV = "mov"           # QuickTime / MOV muxer
    c_MP4 = "mp4"           # MP4 (MPEG-4 Part 14) muxer
    c_MPEG = "mpeg"         # MPEG-1 Systems / MPEG program stream muxer
    c_MPEGTS = "mpegts"     # MPEG-TS (MPEG-2 Transport Stream) muxer
    c_OGG = "ogg"           # Ogg Video muxer
    c_SVCD = "svcd"         # MPEG-2 PS (SVCD) muxer; .vob extension
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
        raise exceptions.UnsupportedVideoFormat(value)

    @staticmethod
    def from_name(name: str) -> 'Container':
        return Container(name.lower())

    def get_supported_video_codecs(self) -> List[str]:
        if self in _EXCLUSIVE_DEMUXERS:
            return _list_supported_video_codecs_for_exclusive_demuxer(self)

        if self.value not in _CONTAINER_SUPPORTED_CODECS:
            return []

        return _CONTAINER_SUPPORTED_CODECS[self.value]["videocodecs"]

    def get_supported_audio_codecs(self) -> List[str]:
        if self in _EXCLUSIVE_DEMUXERS:
            return _list_supported_audio_codecs_for_exclusive_demuxer(self)

        if self.value not in _CONTAINER_SUPPORTED_CODECS:
            return []

        return _CONTAINER_SUPPORTED_CODECS[self.value]["audiocodecs"]

    def get_supported_subtitle_codecs(self) -> List[str]:
        if self in _EXCLUSIVE_DEMUXERS:
            return _list_supported_subtitle_codecs_for_exclusive_demuxer(self)

        if self.value not in _CONTAINER_SUPPORTED_CODECS:
            return []

        return _CONTAINER_SUPPORTED_CODECS[self.value]["subtitlecodecs"]

    def is_supported_video_codec(self, vcodec: Union['codecs.VideoCodec', str]) -> bool:
        if isinstance(vcodec, codecs.VideoCodec):
            return vcodec.value in self.get_supported_video_codecs()
        elif isinstance(vcodec, str):
            return vcodec in self.get_supported_video_codecs()

        assert False, "Invalid type"

    def is_supported_audio_codec(self, acodec: Union['codecs.AudioCodec', str]) -> bool:
        if isinstance(acodec, codecs.AudioCodec):
            return acodec.value in self.get_supported_audio_codecs()
        elif isinstance(acodec, str):
            return acodec in self.get_supported_audio_codecs()

        assert False, "Invalid type"

    def is_supported_subtitle_codec(self, subtitle_codec: Union['codecs.SubtitleCodec', str]) -> bool:
        if isinstance(subtitle_codec, codecs.SubtitleCodec):
            return subtitle_codec.value in self.get_supported_subtitle_codecs()
        elif isinstance(subtitle_codec, str):
            return subtitle_codec in self.get_supported_subtitle_codecs()

        assert False, "Invalid type"

    @staticmethod
    def is_supported(vformat: str) -> bool:
        return vformat in list_supported_formats()

    @staticmethod
    def list_supported_formats() -> List[str]:
        return list_supported_formats()

    def get_demuxer(self) -> str:
        if self not in _DEMUXER_MAP:
            return self.value

        return _DEMUXER_MAP[self].value

    def is_exclusive_demuxer(self) -> bool:
        return self in _EXCLUSIVE_DEMUXERS

    def get_matching_muxers(self) -> Set['Container']:
        muxers = {
            muxer
            for muxer, demuxer in _DEMUXER_MAP.items()
            if demuxer == self
        }

        if self.is_exclusive_demuxer():
            return muxers
        else:
            return muxers | {self}

    def get_intermediate_muxer(self) -> str:
        if self not in _SAFE_INTERMEDIATE_FORMATS:
            return self.value

        return _SAFE_INTERMEDIATE_FORMATS[self].value


# This set containe demuxers that cannot be used as muxers in ffmpeg.
_EXCLUSIVE_DEMUXERS = {
    Container.c_QUICK_TIME_DEMUXER,
    Container.c_MATROSKA_WEBM_DEMUXER,
}


# This dictionary defines which ffmpeg demuxer handles files encoded by which
# muxer. If there's no entry for a particular demuxer, it means that it can
# be used as a demuxer as well.
_DEMUXER_MAP = {
    Container.c_3G2: Container.c_QUICK_TIME_DEMUXER,
    Container.c_3GP: Container.c_QUICK_TIME_DEMUXER,
    Container.c_F4V: Container.c_QUICK_TIME_DEMUXER,
    Container.c_IPOD: Container.c_QUICK_TIME_DEMUXER,
    Container.c_MATROSKA: Container.c_MATROSKA_WEBM_DEMUXER,
    Container.c_MOV: Container.c_QUICK_TIME_DEMUXER,
    Container.c_MP4: Container.c_QUICK_TIME_DEMUXER,
    Container.c_SVCD: Container.c_MPEG,
    Container.c_WEBM: Container.c_MATROSKA_WEBM_DEMUXER,
}
assert set(_DEMUXER_MAP).issubset(set(Container))
assert set(_DEMUXER_MAP.values()).issubset(set(Container))
assert set(_DEMUXER_MAP) & _EXCLUSIVE_DEMUXERS == set()


# It's not possible to tell ffmpeg to preserve the container type. We always
# have to specify the muxer explicitly which is tricky because we only
# know the demuxer and there's no 1:1 mapping between muxers and demuxers.
# This dictionary tells us which muxer can handle all files supported
# by a particular demuxer. If there's no entry for a particular demuxer,
# the assumption is that it's also a muxer and it maps to itself.
_SAFE_INTERMEDIATE_FORMATS = {
    Container.c_MATROSKA_WEBM_DEMUXER: Container.c_MATROSKA,
    Container.c_QUICK_TIME_DEMUXER: Container.c_MOV,
}
assert set(_SAFE_INTERMEDIATE_FORMATS).issubset(set(Container))
assert set(_SAFE_INTERMEDIATE_FORMATS.values()).issubset(set(Container))
assert set(_EXCLUSIVE_DEMUXERS).issubset(set(_SAFE_INTERMEDIATE_FORMATS))


_ASF_CODECS = {
    "videocodecs": [
        "wmv1",
        "wmv2",
        "wmv3",
    ],
    "audiocodecs": [
        "aac",
        "wmav2",
        "wmapro",
    ],
    'subtitlecodecs': [
    ],
}

_MOV_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "hevc",
        "mjpeg",
        "mpeg1video",
        "mpeg2video",

    ],
    "audiocodecs": [
        "mp3",
        "aac",
        "pcm_u8",
    ],
    'subtitlecodecs': [
        'mov_text'
    ],
}

_FLV_CODECS = {
    "videocodecs": [
        "flv1",
    ],
    "audiocodecs": [
        "mp3",
    ],
    'subtitlecodecs': [
    ],
}

_M4V_CODECS = {
    "videocodecs": [
        "h264",
        "mpeg4",
    ],
    "audiocodecs": [
        "aac",
        "ac3",
        "mp3",
    ],
    'subtitlecodecs': [
        'mov_text',
    ],
}

_MP4_CODECS = {
    "videocodecs": [
        "h264",
        "h265",
        "hevc",
        "mpeg4",
    ],
    "audiocodecs": [
        "aac",
        "mp3",
    ],
    'subtitlecodecs': [
        'mov_text',
    ],
}

_MKV_CODECS = {
    "videocodecs": [
        "flv1",
        "h263",
        "h264",
        "h265",
        "hevc",
        "mjpeg",
        "mpeg1video",
        "mpeg2video",
        "mpeg4",
        "msmpeg4v2",
        "theora",
        "vp8",
        "vp9",
        "wmv1",
        "wmv2",
    ],
    "audiocodecs": [
        "mp3",
        "aac",
        "mp3",
        "vorbis",
    ],
    'subtitlecodecs': [
        'ass',
        'subrip',
        'webvtt',
    ],
}

_WEBM_CODECS = {
    "videocodecs": [
        "av1",
        "vp8",
        "vp9",
    ],
    "audiocodecs": [
        "opus",
        "vorbis",
        "vp8",
    ],
    'subtitlecodecs': [
        'webvtt',
    ],
}

_OGG_CODECS = {
    "videocodecs": [
        "theora",
    ],
    "audiocodecs": [
        "opus",
        "vorbis",
    ],
    'subtitlecodecs': [
    ],
}

_AVI_CODECS = {
    "videocodecs": [
        "h264",
        "mjpeg",
        "mpeg1video",
        "mpeg2video",
        "mpeg4",
    ],
    "audiocodecs": [
        "mp3",
        "opus",
    ],
    'subtitlecodecs': [
    ],
}

_3GP_CODECS = {
    "videocodecs": [
        "h263",
        "h264",
        "mpeg4",
    ],
    "audiocodecs": [
        "aac",
        "amr_nb",
    ],
    'subtitlecodecs': [
        'mov_text'
    ],
}

_MPEG_CODECS = {
    "videocodecs": [
        "h264",
        "mpeg1video",
        "mpeg2video",
        "mpeg4",
    ],
    "audiocodecs": [
        "ac3",
        "mp2",
        "mp3",
    ],
    'subtitlecodecs': [
    ],
}


_CONTAINER_SUPPORTED_CODECS = {
    "3g2": _3GP_CODECS,
    "3gp": _3GP_CODECS,
    "avi": _AVI_CODECS,
    "asf": _ASF_CODECS,
    "flv": _FLV_CODECS,
    "ipod": _M4V_CODECS,
    "matroska": _MKV_CODECS,
    "mov": _MOV_CODECS,
    "mp4": _MP4_CODECS,
    "mpeg": _MPEG_CODECS,
    "mpegts": _MPEG_CODECS,
    "ogg": _OGG_CODECS,
    "svcd": _MPEG_CODECS,
    "webm": _WEBM_CODECS,
}
assert set(_CONTAINER_SUPPORTED_CODECS) & {d.value for d in _EXCLUSIVE_DEMUXERS} == set(), \
    "Supported codecs for exclusive demuxers can be determined automatically; no need to define them here"

_aspect_ratio_overrides = {
    "16:9": [
        [426, 240],
        [854, 480],
        [1366, 768],
        [1360, 768]
    ],
    "21:9": [
        [2560, 1080],
        [3440, 1440]
    ]
}


_frame_rates = {
    # NOTE 1: The same frame rate can often be represented a few slightly
    # different ways. For example 24 FPS could be 24, '24', '24/1', '48/2'
    # and so on. Since this list only represents the values we support
    # converting to, we can be picky and choose just one representation as
    # valid.

    # NOTE 2: The common values of 23.976 and 29.97 used to refer to the NTSC
    # frame rates are only approximations. We want to represent them with exact
    # values: 24000/1001 and 30000/1001. This is represented as namedtuple with
    # fields (24000, 1001) and (30000, 1001). All other values are represented
    # the same way, to keep whole dict unified. Values in tuple are int type,
    # there are no floats allowed

    frame_rate.FrameRate(24000, 1001),  # 23.976 FPS (NTSC)
    frame_rate.FrameRate(12),
    frame_rate.FrameRate(15),
    frame_rate.FrameRate(24),
    frame_rate.FrameRate(25),
    frame_rate.FrameRate(30000, 1001),  # 29.97 FPS (NTSC)
    frame_rate.FrameRate(30),
    frame_rate.FrameRate(50),
    frame_rate.FrameRate(60),
    frame_rate.FrameRate(240),
    frame_rate.FrameRate(1000),
}

assert all(isinstance(x.dividend, int) for x in _frame_rates)
assert all(isinstance(x.divisor, int) for x in _frame_rates)


def list_supported_formats() -> List[str]:
    return [c.value for c in Container]


def is_supported(vformat: str) -> bool:
    return Container.is_supported(vformat)


def get_safe_intermediate_format_for_demuxer(demuxer: str) -> str:
    return Container(demuxer).get_intermediate_muxer()


def list_supported_video_codecs(vformat: str) -> List[str]:
    if vformat not in Container._value2member_map_:
        return []

    return Container(vformat).get_supported_video_codecs()


def is_supported_video_codec(vformat: str, codec: str) -> bool:
    return codec in list_supported_video_codecs(vformat)


def _list_supported_video_codecs_for_exclusive_demuxer(demuxer: Container) -> List[str]:
    assert demuxer in _EXCLUSIVE_DEMUXERS

    return list(set(
        codec
        for muxer in demuxer.get_matching_muxers()
        for codec in muxer.get_supported_video_codecs()
    ))


def list_supported_audio_codecs(vformat: str) -> List[str]:
    if vformat not in Container._value2member_map_:
        return []

    return Container(vformat).get_supported_audio_codecs()


def is_supported_audio_codec(vformat: str, codec: str) -> bool:
    return codec in list_supported_audio_codecs(vformat)


def _list_supported_audio_codecs_for_exclusive_demuxer(demuxer: Container) -> List[str]:
    assert demuxer in _EXCLUSIVE_DEMUXERS

    return list(set(
        codec
        for muxer in demuxer.get_matching_muxers()
        for codec in muxer.get_supported_audio_codecs()
    ))


def list_supported_subtitle_codecs(vformat: str) -> List[str]:
    if vformat not in Container._value2member_map_:
        return []

    return Container(vformat).get_supported_subtitle_codecs()


def is_supported_subtitle_codec(vformat: str, codec: str) -> bool:
    return codec in list_supported_subtitle_codecs(vformat)


def _list_supported_subtitle_codecs_for_exclusive_demuxer(demuxer: Container) -> List[str]:
    assert demuxer in _EXCLUSIVE_DEMUXERS

    return list(set(
        codec
        for muxer in demuxer.get_matching_muxers()
        for codec in muxer.get_supported_subtitle_codecs()
    ))


def get_effective_aspect_ratio(resolution: list) -> str:
    for aspect, resolutions_list in _aspect_ratio_overrides.items():
        if resolution in resolutions_list:
            return aspect
    return calculate_aspect_ratio(resolution)


def calculate_aspect_ratio(resolution: list) -> str:
    assert len(resolution) == 2
    resolution_gcd = gcd(resolution[0], resolution[1])
    return f"{resolution[0] // resolution_gcd}:{resolution[1] // resolution_gcd}"


def list_supported_frame_rates() -> Set[frame_rate.FrameRate]:
    return _frame_rates
