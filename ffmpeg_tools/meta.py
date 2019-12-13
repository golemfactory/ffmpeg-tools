import json
from typing import Any, Dict, List, Optional, Union

from . import commands
from . import exceptions


def get_metadata(video):

    try:
        metadata_str = commands.get_metadata_str(video)
        return json.loads(metadata_str)
    except exceptions.CommandFailed:
        return {}


def get_resolution(metadata: Dict['str', Any]) -> List[Any]:
    resolutions = get_resolutions(metadata)
    return resolutions[0] if len(resolutions) > 0 else [0, 0]


def get_resolutions(metadata: Dict['str', Any]) -> List[List[Any]]:
    return [
        [stream.get('width'), stream.get('height')]
        for stream in metadata.get('streams', [])
        if stream.get('codec_type') == 'video'
    ]


def get_frame_rate(metadata: Dict['str', Any]) -> Optional[Any]:
    frame_rates = get_frame_rates(metadata)
    return frame_rates[0] if len(frame_rates) > 0 else None


def get_frame_rates(metadata: Dict['str', Any]) -> List[Any]:
    return get_attribute_from_all_streams(metadata, 'r_frame_rate', 'video')


def _try_int(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return int(value)
        except (TypeError, ValueError):
            pass

    return value


def get_sample_rates(metadata: Dict[str, Any]) -> List[Union[str, int]]:
    return [
        # Sample rates should always be integers but just in case we get a weird
        # file for which ffprobe reports garbage, we'll return raw values if
        # they cannot be converted. That's more useful that just refusing to work
        # and it's the job of validations to reject these values if they're invalid.
        _try_int(s)
        for s in get_attribute_from_all_streams(
            metadata,
            'sample_rate',
            'audio'
        )
    ]


def get_duration(metadata, stream=0):
    return float(metadata["format"]["duration"])


def get_codecs(
    metadata: Dict['str', Any],
    codec_type: str=None) -> List[Any]:

    return get_attribute_from_all_streams(metadata, 'codec_name', codec_type)


def get_video_codec(metadata: Dict['str', Any]) -> Any:
    codecs = get_codecs(metadata, 'video')
    return codecs[0] if len(codecs) > 0 else ""


def get_audio_codec(metadata: Dict['str', Any]) -> Any:
    codecs = get_codecs(metadata, 'audio')
    return codecs[0] if len(codecs) > 0 else ""


def get_format(metadata):
    return metadata["format"]["format_name"]


def get_audio_stream(metadata: Dict['str', Any]) -> Optional[Any]:
    streams = get_streams(metadata, 'audio')
    return streams[0] if len(streams) > 0 else None


def get_streams(
    metadata: Dict['str', Any],
    codec_type: str=None) -> Dict['str', Any]:

    return [
        stream
        for stream in metadata.get('streams', [])
        if (
            codec_type is None or
            stream.get('codec_type') == codec_type
        )
    ]


def count_streams(
    metadata: Dict['str', Any],
    codec_type: str=None) -> int:

    return len(find_stream_indexes(metadata, codec_type))


def find_stream_indexes(
    metadata: Dict['str', Any],
    codec_type: str=None) -> List[Any]:

    return get_attribute_from_all_streams(metadata, 'index', codec_type)


def get_attribute_from_all_streams(
    metadata: Dict['str', Any],
    attribute: str,
    codec_type: str=None) -> List[Any]:

    return [
        stream.get(attribute)
        for stream in metadata.get('streams', [])
        if (
            codec_type is None or
            stream.get('codec_type') == codec_type
        )
    ]


def create_params(
    container,
    resolution,
    vcodec,
    acodec=None,
    frame_rate=None,
    video_bitrate=None,
    audio_bitrate=None,
    scaling_algorithm=None,
):

    args = {}

    args["container"] = container

    # Video parameters
    args["video"] = {}

    args["resolution"] = resolution
    args["video"]["codec"] = vcodec

    if video_bitrate:
        args["video"]["bitrate"] = video_bitrate

    if scaling_algorithm:
        args["scaling_alg"] = scaling_algorithm

    if frame_rate:
        args["frame_rate"] = frame_rate

    # Audio parameters
    if acodec or audio_bitrate:
        args["audio"] = {}

    if acodec:
        args["audio"]["codec"] = acodec

    if audio_bitrate:
        args["audio"]["bitrate"] = audio_bitrate

    return args
