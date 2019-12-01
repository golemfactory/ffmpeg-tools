import os
from typing import Any, Dict, List, Optional, Set, Union

from . import meta
from . import formats
from . import frame_rate
from . import codecs
from . import commands
from . import exceptions


_MAX_SUPPORTED_AUDIO_CHANNELS = 2


def validate_video(metadata):
    try:
        validate_format_metadata(metadata)

        video_format = meta.get_format(metadata)
        validate_format(video_format)
        validate_video_stream_existence(metadata=metadata)

        for stream in metadata['streams']:
            validate_stream(stream, video_format)

    except KeyError:
        raise exceptions.InvalidVideo(message="Video with invalid metadata")
    return True


def _get_dst_audio_codec(dst_params: dict, dst_muxer_info: Optional[Dict[str, Any]]) -> Optional[str]:
    assert not formats.Container(dst_params["container"]).is_exclusive_demuxer()

    if dst_params.get("audio", {}).get("codec") is None:
        if dst_muxer_info is None:
            return None

        return dst_muxer_info.get('default_audio_codec')

    return dst_params['audio']['codec']


def validate_transcoding_params(
    dst_params,
    src_metadata,
    dst_muxer_info = None,
    dst_audio_encoder_info = None,
    strip_unsupported_data_streams=False,
    strip_unsupported_subtitle_streams=False,
):
    """
    Validates the transcoding parameters. Fails if the operation
    is not possible or may result in a video that's damaged or not conforming
    to the specified parameters.

    :param dst_params: dictionary containing transcoding parameters.
    :param dst_params: dictionary with metadata obtained by running ffprobe on
        the source video.
    :param dst_muxer_info: General information about the target container.
        The function uses it for example to determine the defaults ffmpeg will use
        for parameters not specified explicitly. Not providing this information
        makes it impossible to validate those parameters.
        Note: this should be the result of running query_muxer_info().
        It needs to be provided by the caller because the validations might
        not be running on the same machine that does the video processing
        and might not even have access to ffmpeg.
        You can opt out of providing this information and validating the parameters
        whose value was not set explicitly by setting the parameter to None.
    :param strip_unsupported_data_streams: If true, data streams using
        codecs not listed in DATA_STREAM_WHITELIST will not be validated because
        the replace command is going to strip them anyway.
    :param strip_unsupported_subtitle_streams: If true, subtitle streams using
        codecs not listed in SUBTITLE_STREAM_WHITELIST will not be validated because
        the replace command is going to strip them anyway.
    """

    # Validate format
    validate_format(meta.get_format(src_metadata))
    validate_target_format(dst_params['container'])

    # Validate video codec
    validate_video_codecs(meta.get_format(src_metadata), meta.get_codecs(src_metadata, codec_type='video'))
    validate_video_codecs(dst_params['container'], [dst_params["video"]["codec"]])

    for src_video_codec in meta.get_codecs(src_metadata, 'video'):
        validate_video_codec_conversion(src_video_codec, dst_params["video"]["codec"])

    # Validate audio codec. Audio codec can not be set and ffmpeg should
    # either remain with currently used codec or transcode using default behavior
    # if it is necessary.
    if meta.count_streams(src_metadata, 'audio') > 0:
        validate_audio_codecs(meta.get_format(src_metadata), meta.get_codecs(src_metadata, codec_type='audio'))

        dest_audio_codec = _get_dst_audio_codec(dst_params, dst_muxer_info)
        if dest_audio_codec is not None:
            validate_audio_codecs(dst_params["container"], [dest_audio_codec])
            for audio_stream in meta.get_streams(src_metadata, 'audio'):
                validate_audio_codec_conversion(
                    audio_stream.get('codec_name'),
                    dest_audio_codec,
                    audio_stream.get('channels'),
                )

            validate_audio_sample_rates(
                src_metadata,
                dest_audio_codec,
                dst_audio_encoder_info)
        elif dst_muxer_info is not None:
            # Treat situations of user opting out of providing muxer info (dst_muxer_info == None)
            # and ffmpeg not having the info we need ('default_audio_codec' not present in
            # dst_muxer_info or empty) differently.
            raise exceptions.UnsupportedAudioCodecConversion(meta.get_codecs(src_metadata, 'audio'), dest_audio_codec)

    # Validate resolution change
    for resolution in meta.get_resolutions(src_metadata):
        validate_resolution(resolution, dst_params["resolution"])

    for frame_rate in meta.get_frame_rates(src_metadata):
        validate_frame_rate(dst_params, frame_rate)

    validate_unsupported_data_streams(
        src_metadata,
        strip_unsupported_data_streams)
    validate_unsupported_subtitle_streams(
        src_metadata,
        strip_unsupported_subtitle_streams,
        dst_params['container'])
    return True


def _get_extension_from_filename(filename):
    return os.path.splitext(filename)[1][1:]


def validate_format(video_format):
    if video_format not in formats.list_supported_formats():
        raise exceptions.UnsupportedVideoFormat(video_format=video_format)
    return True


def validate_target_format(video_format):
    validate_format(video_format)

    if formats.Container(video_format).is_exclusive_demuxer():
        raise exceptions.UnsupportedTargetVideoFormat(video_format=video_format)
    return True


def validate_format_metadata(metadata):
    try:
        if meta.get_format(metadata) in ['', None]:
            raise exceptions.InvalidFormatMetadata(message="No format names")
    except KeyError:
        raise exceptions.InvalidFormatMetadata("Invalid format metadata")
    return True


def validate_video_stream_existence(metadata):
    if meta.count_streams(metadata, 'video') == 0:
        raise exceptions.MissingVideoStream()

    return True


def validate_stream(stream, video_format):
    if stream["codec_type"].lower() == "video":
        validate_video_stream(stream_metadata=stream, video_format=video_format)
    elif stream["codec_type"].lower() == "audio":
        validate_audio_stream(stream_metadata=stream, video_format=video_format)
    return True


def validate_audio_stream(stream_metadata, video_format):
    try:
        validate_audio_codecs(video_format=video_format, audio_codecs=[stream_metadata["codec_name"]])
    except KeyError:
        raise exceptions.InvalidVideo(message="Audio stream without specified codec")
    return True


def validate_video_stream(stream_metadata, video_format):
    try:
        validate_video_codecs(video_format=video_format, video_codecs=[stream_metadata["codec_name"]])
    except KeyError:
        raise exceptions.InvalidVideo(message="Video stream without specified codec")
    return True


def validate_unsupported_data_streams(metadata: dict, strip_unsupported_data_streams: bool):
    unsupported_data_streams = commands.find_unsupported_data_streams(metadata)

    if not strip_unsupported_data_streams and len(unsupported_data_streams) != 0:
        raise exceptions.UnsupportedStream('data', unsupported_data_streams)

    return True


def validate_unsupported_subtitle_streams(
    metadata: dict,
    strip_unsupported_subtitle_streams: bool,
    target_container: str
):
    if target_container is None:
        # NOTE: Currently this situation is impossible (we'll never get target_container==None
        # because it would not pass other validations) but let's check it just to make sure
        # it does not pass unnoticed if those other validations ever change.
        raise exceptions.InvalidVideo(
            message="Can't know which subtitle codec is supported by the target "
                    "container if that container is not known"
        )

    unsupported_subtitle_streams = commands.find_unsupported_subtitle_streams(metadata, target_container)

    if not strip_unsupported_subtitle_streams and len(unsupported_subtitle_streams) != 0:
        raise exceptions.UnsupportedSubtitleCodecConversion('subtitle', unsupported_subtitle_streams)

    return True


def validate_video_codecs(video_format, video_codecs):
    assert formats.is_supported(video_format)

    for video_codec in video_codecs:
        if not formats.is_supported_video_codec(vformat=video_format, codec=video_codec):
            raise exceptions.UnsupportedVideoCodec(video_codec=video_codec, video_format=video_format)

    return True


def validate_audio_codecs(video_format, audio_codecs):
    assert formats.is_supported(video_format)

    for audio_codec in audio_codecs:
        if not formats.is_supported_audio_codec(vformat=video_format, codec=audio_codec):
            raise exceptions.UnsupportedAudioCodec(audio_codec=audio_codec, video_format=video_format)

    return True


def validate_resolution(src_resolution, target_resolution):
    """
    Validate if aspect ratio of source resolution and
    target resolution are the same.
    """
    if formats.get_effective_aspect_ratio(src_resolution) == \
            formats.get_effective_aspect_ratio(target_resolution):
        return True
    raise exceptions.InvalidResolution(src_resolution, target_resolution)


def _guess_target_frame_rate_for_special_cases(
        src_frame_rate: 'frame_rate.FrameRate',
        dst_video_codec: str) -> Optional['frame_rate.FrameRate']:

    normalized_src_rate = src_frame_rate.normalized()

    if dst_video_codec in codecs.MAX_SUPPORTED_FRAME_RATE:
        max_supported_fps = codecs.MAX_SUPPORTED_FRAME_RATE[dst_video_codec]
        if normalized_src_rate.to_float() > max_supported_fps:
            return frame_rate.FrameRate(max_supported_fps)

    substitution_needed = (
        dst_video_codec in codecs.FRAME_RATE_SUBSTITUTIONS and
        normalized_src_rate in codecs.FRAME_RATE_SUBSTITUTIONS[dst_video_codec])
    if substitution_needed:
        return codecs.FRAME_RATE_SUBSTITUTIONS[dst_video_codec][normalized_src_rate]

    return None


def _guess_target_frame_rate(
        src_frame_rate: 'frame_rate.FrameRate',
        dst_params: Dict[str, Any]) -> 'frame_rate.FrameRate':

    target_frame_rate = _guess_target_frame_rate_for_special_cases(
        src_frame_rate,
        dst_params['video']['codec'],
    )
    return target_frame_rate if target_frame_rate is not None else src_frame_rate


def validate_frame_rate(
        dst_params: Dict[str, Any],
        src_frame_rate: Optional[str]) -> bool:

    if 'frame_rate' in dst_params:
        try:
            target_frame_rate = frame_rate.FrameRate.decode(dst_params['frame_rate'])
        except ValueError as exception:
            raise exceptions.InvalidFrameRate(src_frame_rate, dst_params['frame_rate'])
    else:
        if src_frame_rate is None:
            raise exceptions.InvalidFrameRate(None, dst_params.get('frame_rate'))

        try:
            decoded_src_frame_rate = frame_rate.FrameRate.decode(src_frame_rate)
        except ValueError as exception:
            raise exceptions.InvalidFrameRate(src_frame_rate, None)

        target_frame_rate = _guess_target_frame_rate(
            decoded_src_frame_rate,
            dst_params,
        )

    if target_frame_rate.normalized() not in formats.list_supported_frame_rates():
        raise exceptions.InvalidFrameRate(src_frame_rate, target_frame_rate)
    return True


def validate_audio_sample_rates(
        src_metadata: Dict[str, Any],
        dest_audio_codec: str,
        dst_audio_encoder_info: Optional[Dict[str, Any]]) -> bool:

    assert dest_audio_codec in codecs.AudioCodec._value2member_map_
    assert codecs.AudioCodec(dest_audio_codec).get_encoder() is not None

    for src_sample_rate in meta.get_sample_rates(src_metadata):
        supported = codecs.is_supported_sample_rate(
            dest_audio_codec,
            src_sample_rate,
            dst_audio_encoder_info,
        )
        if not supported:
            raise exceptions.UnsupportedSampleRate(src_sample_rate, dest_audio_codec)

    return True


def validate_video_codec_conversion(src_codec, dst_codec):
    codec = codecs.VideoCodec(src_codec)
    if dst_codec not in codec.get_supported_conversions():
        raise exceptions.UnsupportedVideoCodecConversion(src_codec, dst_codec)
    return True


def validate_audio_codec_conversion(src_codec, dst_codec, src_channel_count):
    codec = codecs.AudioCodec(src_codec)

    if dst_codec not in codec.get_supported_conversions():
        raise exceptions.UnsupportedAudioCodecConversion(src_codec, dst_codec)

    if src_codec != dst_codec and (src_channel_count is None or src_channel_count > _MAX_SUPPORTED_AUDIO_CHANNELS):
        # Multi-channel audio is not supported by all audio codecs.
        # We want to avoid creating another list to keep this information,
        # so we’ll just assume that if we found multi-channel audio in the input,
        # it’s OK and otherwise it’s not supported.
        raise exceptions.UnsupportedAudioChannelLayout(src_channel_count)

    return True
