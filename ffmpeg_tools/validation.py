import os
from math import gcd
from typing import Any, Dict, Optional, Union

from . import meta
from . import formats
from . import codecs
from . import commands


_MAX_SUPPORTED_AUDIO_CHANNELS = 2


class InvalidVideo(Exception):
    def __init__(self, message):
        super().__init__()
        self.response_message = message


class UnsupportedVideoFormat(InvalidVideo):
    def __init__(self, video_format):
        super().__init__(message="Unsupported video format: {}".format(video_format))


class UnsupportedTargetVideoFormat(InvalidVideo):
    def __init__(self, video_format):
        super().__init__(message="Muxing not supported for video format: {}".format(video_format))


class UnsupportedVideoCodec(InvalidVideo):
    def __init__(self, video_codec, video_format):
        super().__init__(message="Unsupported video codec: {} for video format: {}".format(video_codec, video_format))


class UnsupportedAudioCodec(InvalidVideo):
    def __init__(self, audio_codec, video_format):
        super().__init__(message="Unsupported audio codec: {} for video format: {}".format(audio_codec, video_format))


class MissingVideoStream(InvalidVideo):
    def __init__(self):
        super().__init__(message="Missing video stream")


class InvalidFormatMetadata(InvalidVideo):
    def __init__(self, message):
        super().__init__(message=message)


class InvalidResolution(InvalidVideo):
    def __init__(self, src_resolution, target_resolution):
        super().__init__(message="Unsupported resolution conversion from {} to {}.".format(src_resolution, target_resolution))


class InvalidFrameRate(InvalidVideo):
    def __init__(self, src_frame_rate, target_frame_rate):
        super().__init__(message="Unsupported frame rate conversion from {} to {}.".format(src_frame_rate, target_frame_rate))


class UnsupportedVideoCodecConversion(InvalidVideo):
    def __init__(self, src_codec, dst_codec):
        super().__init__(message="Unsupported video codec conversion from {} to {}".format(src_codec, dst_codec))


class UnsupportedAudioCodecConversion(InvalidVideo):
    def __init__(self, src_codec, dst_codec):
        super().__init__(message="Unsupported audio codec conversion from {} to {}".format(src_codec, dst_codec))


class UnsupportedStream(InvalidVideo):
    def __init__(self, stream_type, index):
        super().__init__(message="Unsupported {} stream. Stream index: {}."
                         .format(stream_type, index))


class UnsupportedAudioChannelLayout(InvalidVideo):
    def __init__(self, audio_channels):
        super().__init__(
            message="Unsupported audio channel layout conversion. "
                    "Unable to reliably preserve the {}-channel audio found "
                    "in the input file in combination with other target parameters.".format(audio_channels)
        )


def validate_video(metadata):
    try:
        validate_format_metadata(metadata)

        video_format = meta.get_format(metadata)
        validate_format(video_format)
        validate_video_stream_existence(metadata=metadata)

        for stream in metadata['streams']:
            validate_stream(stream, video_format)

    except KeyError:
        raise InvalidVideo(message="Video with invalid metadata")
    return True


def validate_data_and_subtitle_streams(
    metadata,
    strip_unsupported_data_streams,
    strip_unsupported_subtitle_streams,
):
    (unsupported_data_streams, unsupported_subtitle_streams) = (
        commands.get_lists_of_unsupported_stream_numbers(metadata)
    )
    if not strip_unsupported_data_streams and len(unsupported_data_streams) != 0:
        raise UnsupportedStream('data', unsupported_data_streams)

    if not strip_unsupported_subtitle_streams and len(unsupported_subtitle_streams) != 0:
        raise UnsupportedStream('subtitle', unsupported_subtitle_streams)


def validate_transcoding_params(
    dst_params,
    src_metadata,
    strip_unsupported_data_streams=False,
    strip_unsupported_subtitle_streams=False,
):

    src_params = meta.create_params(
        meta.get_format(src_metadata),
        meta.get_resolution(src_metadata),
        meta.get_video_codec(src_metadata),
        meta.get_audio_codec(src_metadata),
        meta.get_frame_rate(src_metadata))

    # Validate format
    validate_format(src_params["format"])
    validate_target_format(dst_params["format"])

    # Validate video codec
    validate_video_codec(src_params["format"], src_params["video"]["codec"])
    validate_video_codec(dst_params["format"], dst_params["video"]["codec"])
    validate_video_codec_conversion(src_params["video"]["codec"], dst_params["video"]["codec"])

    # Validate audio codec. Audio codec can not be set and ffmpeg should
    # either remain with currently used codec or transcode using default behavior
    # if it is necessary.
    try:
        validate_audio_codec(src_params["format"], src_params["audio"]["codec"])
        validate_audio_codec(dst_params["format"], dst_params["audio"]["codec"])
        validate_audio_codec_conversion(
            src_params["audio"]["codec"],
            dst_params["audio"]["codec"],
            meta.get_audio_stream(src_metadata)
        )
    except KeyError as _:
        # We accept only KeyError, because it means, there were now value
        # in dictionary. Note that validate functions can still throw other
        # exceptions in case of invalid parameters.
        pass

    # Validate resolution change
    validate_resolution(src_params["resolution"], dst_params["resolution"])

    validate_frame_rate(dst_params, src_params["frame_rate"])

    validate_data_and_subtitle_streams(
        src_metadata,
        strip_unsupported_data_streams,
        strip_unsupported_subtitle_streams)
    return True


def _get_extension_from_filename(filename):
    return os.path.splitext(filename)[1][1:]


def validate_format(video_format):
    if video_format not in formats.list_supported_formats():
        raise UnsupportedVideoFormat(video_format=video_format)
    return True


def validate_target_format(video_format):
    validate_format(video_format)

    if formats.Container(video_format).is_exclusive_demuxer():
        raise UnsupportedTargetVideoFormat(video_format=video_format)
    return True


def validate_format_metadata(metadata):
    try:
        if meta.get_format(metadata) in ['', None]:
            raise InvalidFormatMetadata(message="No format names")
    except KeyError:
        raise InvalidFormatMetadata("Invalid format metadata")
    return True


def validate_video_stream_existence(metadata):
    try:
        for stream in metadata['streams']:
            if stream["codec_type"].lower() == "video":
                return True
    except KeyError:
        raise InvalidVideo("Invalid stream metadata")

    raise MissingVideoStream()
    return True


def validate_stream(stream, video_format):
    if stream["codec_type"].lower() == "video":
        validate_video_stream(stream_metadata=stream, video_format=video_format)
    elif stream["codec_type"].lower() == "audio":
        validate_audio_stream(stream_metadata=stream, video_format=video_format)
    return True


def validate_audio_stream(stream_metadata, video_format):
    try:
        validate_audio_codec(video_format=video_format, audio_codec=stream_metadata["codec_name"])
    except KeyError:
        raise InvalidVideo(message="Audio stream without specified codec")
    return True


def validate_video_stream(stream_metadata, video_format):
    try:
        validate_video_codec(video_format=video_format, video_codec=stream_metadata["codec_name"])
    except KeyError:
        raise InvalidVideo(message="Video stream without specified codec")
    return True


def validate_video_codec(video_format, video_codec):
    if not formats.is_supported_video_codec(vformat=video_format, codec=video_codec):
        raise UnsupportedVideoCodec(video_codec=video_codec, video_format=video_format)
    return True


def validate_audio_codec(video_format, audio_codec):
    if not formats.is_supported_audio_codec(vformat=video_format, codec=audio_codec):
        raise UnsupportedAudioCodec(audio_codec=audio_codec, video_format=video_format)
    return True


def validate_resolution(src_resolution, target_resolution):
    """
    Validate if aspect ratio of source resolution and
    target resolution are the same.
    """
    if formats.get_effective_aspect_ratio(src_resolution) == \
            formats.get_effective_aspect_ratio(target_resolution):
        return True
    raise InvalidResolution(src_resolution, target_resolution)


def _try_get_frame_rate_based_for_corner_cases(
        src_frame_rate: str,
        dst_video_codec: str) -> Optional[Union[int, 'formats.FrameRate']]:

    normalized_src_rate = src_frame_rate.normalized()

    if dst_video_codec in codecs.MAX_SUPPORTED_FRAME_RATE:
        (dividend, divisor) = normalized_src_rate
        return min(
            dividend // divisor,
            codecs.MAX_SUPPORTED_FRAME_RATE[dst_video_codec]
        )

    if dst_video_codec in codecs.FRAME_RATE_SUBSTITUTIONS:
        for (original, substitute) in codecs.FRAME_RATE_SUBSTITUTIONS[dst_video_codec]:
            assert original == original.normalized()

            if normalized_src_rate == original:
                return substitute

    return None


def _get_frame_rate_based_on_src_frame_rate(
        src_frame_rate: str,
        dst_params: Dict[str, Any]) -> str:

    target_frame_rate = _try_get_frame_rate_based_for_corner_cases(
        src_frame_rate,
        dst_params['video']['codec'],
    )
    return target_frame_rate if target_frame_rate is not None else src_frame_rate


def validate_frame_rate(
        dst_params: Dict[str, Any],
        src_frame_rate: str) -> bool:

    if 'frame_rate' in dst_params:
        target_frame_rate = dst_params['frame_rate']
    else:
        target_frame_rate = _get_frame_rate_based_on_src_frame_rate(src_frame_rate, dst_params)

    if formats.FrameRate.decode(target_frame_rate).normalized() not in formats.list_supported_frame_rates():
        raise InvalidFrameRate(src_frame_rate, target_frame_rate)
    return True


def validate_video_codec_conversion(src_codec, dst_codec):
    codec = codecs.VideoCodec(src_codec)
    if dst_codec not in codec.get_supported_conversions():
        raise UnsupportedVideoCodecConversion(src_codec, dst_codec)
    return True


def validate_audio_codec_conversion(src_codec, dst_codec, audio_stream):
    codec = codecs.AudioCodec(src_codec)
    if dst_codec not in codec.get_supported_conversions():
        raise UnsupportedAudioCodecConversion(src_codec, dst_codec)
    if src_codec != dst_codec and \
            audio_stream['channels'] > _MAX_SUPPORTED_AUDIO_CHANNELS:
        # Multi-channel audio is not supported by all audio codecs.
        # We want to avoid creating another list to keep this information,
        # so we’ll just assume that if we found multi-channel audio in the input,
        # it’s OK and otherwise it’s not supported.
        raise UnsupportedAudioChannelLayout(audio_stream['channels'])
    return True
