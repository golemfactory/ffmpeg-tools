import enum

from . import validation



class VideoCodec(enum.Enum):
    H_264 = 'h264'
    H_265 = 'h265'
    HEVC = 'HEVC'
    MPEG_1 = 'mpeg1video'
    MPEG_2 = 'mpeg2video'
    MPEG_4 = 'mpeg4'


    # Normally enum throws ValueError, when initialization value is invalid.
    # We want to return more meaningful exception. This function is called by
    # enum when all conversion options failed.
    @classmethod
    def _missing_(cls, value):
        raise validation.UnsupportedVideoCodec(value, "")

    @staticmethod
    def from_name(name: str) -> 'VideoCodec':
        return VideoCodec(name)

    # FFMPEG needs encoder name, instead of codec name as transcoding parameter.
    # If list doesn't contain encoder we assume that we can pass codec name.
    def get_encoder(self):
        return _VIDEO_ENCODERS.get(self.value, self.value)

    def get_supported_conversions(self):
        return _VIDEO_SUPPORTED_CONVERSIONS.get(self.value, [])


class AudioCodec(enum.Enum):
    AAC = 'aac'
    MP3 = 'mp3'


    # Normally enum throws ValueError, when initialization value is invalid.
    # We want to return more meaningful exception. This function is called by
    # enum when all conversion options failed.
    @classmethod
    def _missing_(cls, value):
        raise validation.UnsupportedAudioCodec(value, "")

    @staticmethod
    def from_name(name: str) -> 'AudioCodec':
        return AudioCodec(name)

    # FFMPEG needs encoder name, instead of codec name as transcoding parameter.
    # If list doesn't contain encoder we assume that we can pass codec name.
    def get_encoder(self):
        return _AUDIO_ENCODERS.get(self.value, self.value)

    def get_supported_conversions(self):
        return _AUDIO_SUPPORTED_CONVERSIONS.get(self.value, [])



_VIDEO_ENCODERS = {
    "h264": "libx264",
    "h265": "libx265",
    "HEVC": "libx265",
    "mpeg1video": "mpeg1video",
    "mpeg2video": "mpeg2video",
    "mpeg4": "libxvid"
}

_AUDIO_ENCODERS = {
    "aac": "aac",
    "mp3": "libmp3lame"
}


_VIDEO_SUPPORTED_CONVERSIONS = {
    "h264" : [ "h264", "h265" ]
}

_AUDIO_SUPPORTED_CONVERSIONS = {
    "aac": [ "aac" ],
    "mp3": [ "mp3" ],
}


def get_video_encoder(target_codec):
    # This will throw exception for unsupported codecs.
    codec = VideoCodec(target_codec)
    return codec.get_encoder()


def get_audio_encoder(target_codec):
    # This will throw exception for unsupported codecs.
    codec = AudioCodec(target_codec)
    return codec.get_encoder()


def list_supported_video_conversions(codec):
    try:
        vcodec = VideoCodec(codec)
        return vcodec.get_supported_conversions()
    except:
        return []


def list_supported_audio_conversions(codec):
    try:
        acodec = AudioCodec(codec)
        return acodec.get_supported_conversions()
    except:
        return []