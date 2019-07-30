import json

from . import commands


def get_metadata(video):

    try:
        metadata_str = commands.get_metadata_str(video)
        return json.loads(metadata_str)
    except commands.CommandFailed:
        return {}


def get_resolution(metadata):
    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            return [stream["width"], stream["height"]]
    return [0, 0]


def get_frame_rate(metadata):
    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            return stream["r_frame_rate"]
    return None


def get_duration(metadata, stream=0):
    return float(metadata["format"]["duration"])


def get_video_codec(metadata):
    for stream in metadata["streams"]:
        if stream["codec_type"] == "video":
            return stream["codec_name"]
    return ""


def get_audio_codec(metadata):
    for stream in metadata["streams"]:
        if stream["codec_type"] == "audio":
            return stream["codec_name"]
    return ""


def get_format(metadata):
    return metadata["format"]["format_name"]


def get_audio_stream(metadata):
    for stream in metadata['streams']:
        if stream["codec_type"] == "audio":
            return stream
    return None


def create_params(vformat, resolution, vcodec, acodec=None,
                  frame_rate=None, video_bitrate=None,
                  audio_bitrate=None, scaling_algorithm=None):
    args = dict()

    args["format"] = vformat

    # Video parameters
    args["video"] = dict()

    args["resolution"] = resolution
    args["video"]["codec"] = vcodec

    if video_bitrate:
        args["video"]["bitrate"] = video_bitrate

    if scaling_algorithm:
        args["scaling_alg"] = scaling_algorithm

    if frame_rate:
        args["frame_rate"] = frame_rate

    # Audio parameters
    args["audio"] = dict()

    if acodec:
        args["audio"]["codec"] = acodec

    if audio_bitrate:
        args["audio"]["bitrate"] = audio_bitrate

    return args
