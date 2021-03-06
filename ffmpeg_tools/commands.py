import os
import re
import subprocess
import sys
import json
from typing import Any, Dict, List

from . import codecs
from . import exceptions
from . import meta


FFMPEG_COMMAND = "ffmpeg"
FFPROBE_COMMAND = "ffprobe"

TMP_DIR = "/golem/work/tmp/"


def flatten_list(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]


def exec_cmd(cmd, file=None):
    print("Executing command:")
    print(cmd)

    pc = subprocess.Popen(cmd, stdout=file, stderr=file)

    ret = pc.wait()
    if ret != 0:
        raise exceptions.CommandFailed(cmd, ret)


def exec_cmd_to_file(cmd, filepath):
    # Ensure directory exists
    filedir = os.path.dirname(filepath)
    if not os.path.exists(filedir):
        os.makedirs(filedir)

    # Execute command and send results to file.
    with open(filepath, "w") as result_file:
        exec_cmd(cmd, result_file)


def exec_cmd_to_string(cmd):

    print("Executing command:")
    print(cmd)

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        raise exceptions.CommandFailed(cmd, result.returncode)
    return result.stdout.decode('utf-8')


def extract_streams(input_file,
                    output_file,
                    selected_streams,
                    container=None):
    assert os.path.isfile(input_file)
    assert not os.path.exists(output_file)

    cmd = extract_streams_command(
        input_file,
        output_file,
        selected_streams,
        container)

    exec_cmd(cmd)


def extract_streams_command(input_file,
                            output_file,
                            selected_streams,
                            container=None):
    """
    Builds a ffmpeg command that can be used to extract a selected streams
    from a container and put them in a newly created container of the same type

    :param input_file: Container to extract the streams from. Must exist.
    :param output_file: Container to put the streams in. Must not exist.
    :param selected_streams: List of streams to extract.
        List items should be valid stream selectors when prefixed with `0:`
        See https://trac.ffmpeg.org/wiki/Map.
        A few examples:
           [0, 1, 2]     - first three streams
           ['v']         - all video streams
           ['a', 'd']    - all audio and data streams
           ['v', 'a:2']  - all video streams and third audio stream
    :param container: Video container type for the output file.
    """

    map_options = [
        ["-map", f"0:{index}"]
        for index in selected_streams
    ]

    cmd = (
        [
            FFMPEG_COMMAND,
            "-nostdin",
            "-i", input_file,
        ] +
        flatten_list(map_options) +
        [
            "-codec", "copy",
        ] +
        ([
            "-f", container,
        ] if container is not None else []) +
        [
            output_file,
        ]
    )

    return cmd


def strip_suffix_from_segments_and_rename_files(output_list_file_path, suffix):
    with open(output_list_file_path) as output_list_file:
        file_paths = output_list_file.read().splitlines()

    list_dir = os.path.dirname(output_list_file_path)

    updated_file_list = []
    for file_path in file_paths:
        if not file_path.endswith(suffix):
            # Should not happen if the list contains what we expect but we
            # can't just assume that.
            raise exceptions.InvalidCommandOutput(
                f"Segment name does not match the expected pattern: {file_path}")

        # Segment paths are relative to the location of the list file
        full_file_path = os.path.join(list_dir, file_path)

        new_path = file_path[:-len(suffix)]
        full_new_path = full_file_path[:-len(suffix)]
        if os.path.exists(new_path):
            # This should never happen but is not impossible (filesystem is not
            # under our sole control) so an assert is not appropriate.
            raise exceptions.FileAlreadyExists(
                f"Renaming '{file_path}' to '{new_path}' would overwrite the other file.")

        os.rename(full_file_path, full_new_path)
        updated_file_list.append(new_path)

    with open(output_list_file_path, 'w') as output_list_file:
        output_list_file.write("\n".join(updated_file_list))


def split_video(input_file, output_dir, split_len, container=None):
    [_, filename] = os.path.split(input_file)
    [basename, _] = os.path.splitext(filename)

    output_list_file = os.path.join(output_dir, basename + "-segment-list.txt")

    split_list_file = split(input_file, output_list_file, split_len, container)

    return split_list_file


def split(input_file, output_list_file, segment_time, container=None):
    cmd, file_list = split_video_command(input_file, output_list_file,
                                         segment_time, container)
    exec_cmd(cmd)
    strip_suffix_from_segments_and_rename_files(output_list_file, '.mkv')

    return file_list


def split_video_command(input_file,
                        output_list_file,
                        segment_time,
                        container=None):
    (_, input_filename) = os.path.split(input_file)
    (input_basename, extension) = os.path.splitext(input_filename)

    (output_dir, _) = os.path.split(output_list_file)
    if container is not None:
        # ffmpeg with -segment_format option fails if the output file name
        # pattern has no extension in it or has an extension not supported by
        # ffmpeg. This seems to be a bug, even reported in
        # (https://trac.ffmpeg.org/ticket/4483) but closed as invalid (why?).
        # A simple workaround is to add any valid extension to the pattern.
        # The -segment_format option has priority over the file extension.
        extension += '.mkv'

    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        "-i", input_file,
        "-codec", "copy",
        "-f", "segment",
    ] + ([
        "-segment_format", container,
    ] if container is not None else []) + [
        "-reset_timestamps", "1",
        "-segment_time", f"{segment_time}",
        "-segment_list_type", "flat",
        "-segment_list", output_list_file,
        f"{output_dir}/{input_basename}_%d{extension}",
    ]

    return cmd, output_list_file


def transcode_video(track, targs, output):
    cmd = transcode_video_command(track, output, targs)
    exec_cmd(cmd)


def transcode_video_command(track, output_file, targs):
    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        # process an input file
        "-i",
        # input file
        "{}".format(track),
    ] + ([
        "-f", targs['container'],
    ] if 'container' in targs else [])

    if 'audio' in targs:
        # NOTE: It's not guaranteed that the file passed in here by the caller does not
        # have an audio track unless the file was passed to extract_streams_command() first.
        # If it wasn't, the audio parameters could actually have effect on the output.
        # We assume that it was though, because doing otherwise is not useful in practice.
        # We could inspect the file with ffprobe (again) to be sure but I don't think
        # it's worth it for such a fringe case.
        raise exceptions.InvalidArgument(
            "The 'transcode' command works with a video stream extracted from the input video. "
            "Audio parameters would have no effect when used here. "
            "You should pass them to the 'replace' command instead.")

    # video settings
    if 'video' in targs and 'codec' in targs['video']:
        vcodec = targs['video']['codec']
        cmd.append("-c:v")
        cmd.append(codecs.get_video_encoder(vcodec))
        cmd = cmd + codecs.preserve_quality_command(vcodec)

    if 'frame_rate' in targs:
        fps = str(targs['frame_rate'])
        cmd.append("-r")
        cmd.append(fps)

    if 'video' in targs and 'bitrate' in targs['video']:
        vbitrate = targs['video']['bitrate']
        cmd.append("-b:v")
        cmd.append(vbitrate)

    if 'resolution' in targs:
        res = targs['resolution']
        cmd.append("-vf")
        cmd.append("scale={}:{}".format(res[0], res[1]))

    if 'scaling_alg' in targs:
        scale = targs["scaling_alg"]
        cmd.append("-sws_flags")
        cmd.append("{}".format(scale))

    cmd.append("{}".format(output_file))

    return cmd


def merge_videos(input_files, output, container=None):
    cmd, _list_file = merge_videos_command(
        input_files,
        output,
        container)
    exec_cmd(cmd)


def merge_videos_command(input_file, output, container=None):
    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        "-f", "concat",
        "-safe", "0",
        "-i", input_file,
        "-c", "copy",
    ] + ([
        "-f", container,
    ] if container is not None else []) + [
        output
    ]

    return cmd, input_file


def replace_streams(input_file,
                    replacement_source,
                    output_file,
                    stream_type,
                    targs,
                    container=None,
                    strip_unsupported_data_streams=False,
                    strip_unsupported_subtitle_streams=False):

    assert os.path.isfile(input_file)
    assert os.path.isfile(replacement_source)
    assert not os.path.exists(output_file)

    cmd = replace_streams_command(
        input_file,
        replacement_source,
        output_file,
        stream_type,
        targs,
        container,
        strip_unsupported_data_streams,
        strip_unsupported_subtitle_streams)
    exec_cmd(cmd)


def find_unsupported_data_streams(metadata):
    return [
        stream_metadata.get('index')
        for stream_metadata in metadata.get('streams', [])
        if (
            stream_metadata.get('codec_type') == 'data' and
            stream_metadata.get('codec_name') not in codecs.DATA_STREAM_WHITELIST
        )
    ]


def find_unsupported_subtitle_streams(metadata, target_container):
    if target_container is None:
        # This is a corner case that won't happen if you explicitly select
        # the target container instead of letting ffmpeg select one
        # based on the file name and possibly other factors.
        # It's best to always specify the container but ffmpeg-tools allows
        # you not to do it for the sake of flexibility.
        #
        # If the target container is selected implicitly by ffmpeg, we
        # can't really know which subtitle streams it supports.
        # The safest bet is to say that all subtitle streams are supported.
        # This way nothing gets stripped and ffmpeg either converts them on
        # its own or fails, letting the user know that it can't process the video.
        return []

    return [
        stream_metadata.get('index')
        for stream_metadata in metadata.get('streams', [])
        if (
            stream_metadata.get('codec_type') == 'subtitle' and
            (
                stream_metadata.get('codec_name') not in codecs.SubtitleCodec._value2member_map_ or
                codecs.SubtitleCodec(stream_metadata.get('codec_name')).select_conversion_for_container(target_container) is None
            )
        )
    ]


def select_subtitle_conversions(metadata, target_container):
    if target_container is None:
        # No container specified = leave conversions up to ffmpeg
        return {}

    conversions = {
        stream_metadata.get('index'): codecs.SubtitleCodec(stream_metadata.get('codec_name')).select_conversion_for_container(target_container)
        for stream_metadata in metadata.get('streams', [])
        if (
            stream_metadata.get('codec_type') == 'subtitle' and
            stream_metadata.get('codec_name') in codecs.SubtitleCodec._value2member_map_
        )
    }
    return {index: codec for index, codec in conversions.items() if codec is not None}


def adjust_stream_indexes_for_removals(indexed_map: Dict[int, Any], removed_indexes: List[int]) -> Dict[int, Any]:
    """
    Accepts a dict representing streams that will not be removed
    and updates their indexes to the values they will have when some other
    streams get removed.
    """

    assert set(indexed_map) & set(removed_indexes) == set()
    assert all(index >= 0 for index in set(indexed_map) | set(removed_indexes))

    if len(indexed_map) == 0:
        return {}

    # We'll iterate over two sorted collections in paralled.
    # The first one is the set of streams to be removed.
    # The other is a set of buckets corresponding to intervals between streams
    # from index_map. Initially the buckets are empty. As we go over the
    # removed streams, each one is added to the bucket for interval it falls into.
    removal_histogram = {index: 0 for index in sorted(indexed_map)}
    histogram_iterator = (index for index in removal_histogram)
    current_histogram_index = next(histogram_iterator)

    done = False
    for removed_index in sorted(removed_indexes):
        while current_histogram_index < removed_index:
            try:
                current_histogram_index = next(histogram_iterator)
            except StopIteration:
                done = True
                break

        if done:
            break

        removal_histogram[current_histogram_index] += 1

    # Now we go over each stream in indexed_map and decrease its index by the total
    # number of removed streams below it. We get that running total by summing
    # the buckets as we go.
    reindexed_map: Dict[int, Any] = {}
    running_total = 0
    for index, value in indexed_map.items():
        running_total += removal_histogram[index]
        assert running_total <= index
        assert index - running_total not in reindexed_map

        reindexed_map[index - running_total] = value

    return reindexed_map


def shift_stream_indexes(indexed_map: Dict[int, Any], shift: int) -> Dict[int, Any]:
    assert all(index + shift >= 0 for index in indexed_map)

    return {index + shift: value for index, value in indexed_map.items()}


def replace_streams_command(input_file,
                            replacement_source,
                            output_file,
                            stream_type,
                            targs,
                            container=None,
                            strip_unsupported_data_streams=False,
                            strip_unsupported_subtitle_streams=False):
    """
    Builds a ffmpeg command that can be used to create a new video file with
    all streams of a specific type replaced with streams of the same type from
    another video file.

    :param input_file: Container from which all the streams of types other than
        the specified one will be taken. Must exist.
    :param replacement_source: Container from which streams of the specified
        type will be taken. Must exist.
    :param output_file: Container to put the streams in. Must not exist.
    :param stream_type: Stream type specifier.
        See https://ffmpeg.org/ffmpeg.html#Stream-specifiers.
        The following values are supported:
            - `v` - same as `V`.
            - `V` - video streams which are not attached pictures, video
                    thumbnails or cover arts.
            - `a` - audio streams.
    :param targs: Dictionary with additional transcoding parameters.
        The following parameters are supported:
            - `audio`: dict with parameters for audio stream transcoding.
                Same parameters are applied to all audio streams.
                Transcoding different audio streams differently is currently
                not supported.
                Can include the following keys:`bitrate`, `codec`.
    :param container: Container type to use for the output file.
        Optional, but highly recommended. If you don't specify it, ffmpeg will
        try to guess based the extension of the output file and also we won't
        be able to convert supported subtitles or strip unsupported ones (because
        support depends on container type).
    :param strip_unsupported_data_streams: If true, all data streams using
        codecs not listed in DATA_STREAM_WHITELIST will not be included in the
        output file. If your input_file contains such streams but you don't
        care about them, you can use this option to force a conversion that
        would otherwise fail.
    :param strip_unsupported_subtitle_streams: If true, all subtitle streams
        which are not supported by the target container and cannot be converted
        to any other subtitle type that is supported, will not be included in
        the output file. If your input_file contains such streams but you don't
        care about them, you can use this option to force a conversion that
        would otherwise fail.

        If target container is not specified, all subtitle
        streams are treated as supported. In that case there's no explicit
        conversion but ffmpeg is allowed to convert them if it can (hint: it
        often can but does not want to because there are many possible subtitle
        codecs and no default - it refuses to choose one on its own and fails).
    """
    # NOTE: We could support 's' (subtitle streams) or 'd' (data streams) as well
    # but it would complicate the implementation and we currently don't use them
    # so implementing it was not worth the hassle.
    VALID_STREAM_TYPES = {
        'v': 'video',
        'V': 'video',
        'a': 'audio',
    }
    if stream_type not in VALID_STREAM_TYPES:
        raise exceptions.InvalidArgument(
            f"Invalid value of 'stream_type'. "
            f"Should be one of: {', '.join(VALID_STREAM_TYPES)}"
        )

    if 'video' in targs:
        # The video parameters could have an effect here if we added them to the
        # ffmpeg command but we don't want to. It could result in video
        # being transcoded again - i.e. work that was supposed to be already
        # performed by the 'transcode' command, potentially on a completely
        # different machine.
        raise exceptions.InvalidArgument(
            "The video has already been transcoded so it's too late to specify video parameters. "
            "Then would have no effect when used here. "
            "You should pass them to the 'transcode' command instead.")

    input_metadata = get_metadata_json(input_file)
    replacement_metadata = get_metadata_json(replacement_source)

    if strip_unsupported_data_streams:
        data_streams_to_strip = find_unsupported_data_streams(input_metadata)
    else:
        data_streams_to_strip = []

    data_map_options = [
        ["-map", f"-0:{index}"]
        for index in data_streams_to_strip
    ]

    if strip_unsupported_subtitle_streams:
        subtitle_streams_to_strip = find_unsupported_subtitle_streams(input_metadata, container)
    else:
        subtitle_streams_to_strip = []

    subtitle_map_options = [
        ["-map", f"-0:{index}"]
        for index in subtitle_streams_to_strip
    ]

    subtitle_codec_map = shift_stream_indexes(
        adjust_stream_indexes_for_removals(
            select_subtitle_conversions(input_metadata, container),
            data_streams_to_strip +
            subtitle_streams_to_strip +
            meta.find_stream_indexes(input_metadata, VALID_STREAM_TYPES[stream_type]),
        ),
        meta.count_streams(replacement_metadata, VALID_STREAM_TYPES[stream_type]),
    )
    subtitle_codec_options = [
        [f"-codec:{index}", codec]
        for index, codec in subtitle_codec_map.items()
    ]

    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        "-i", input_file,
        "-i", replacement_source,
        "-map", f"1:{stream_type}",
        "-map", "0",
        "-map", f"-0:{stream_type}",
    ] + flatten_list(data_map_options) + [
    ] + flatten_list(subtitle_map_options) + [
    ] + flatten_list(subtitle_codec_options) + [
        "-copy_unknown",
        "-c:v", "copy",
        "-c:d", "copy",
    ] + ([
        "-f", container,
    ] if container is not None else []) + ([
        "-c:a", codecs.get_audio_encoder(targs['audio']['codec']),
    ] if 'codec' in targs.get('audio', {}) else []) + ([
        "-b:a", targs['audio']['bitrate'],
    ] if 'bitrate' in targs.get('audio', {}) else []) + [
        output_file,
    ]

    return cmd


def compute_psnr_command(video, reference_video, psnr_frames_file):
    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        "-i", video,
        "-i", reference_video,
        "-lavfi",
        "psnr=" + psnr_frames_file,
        "-f", "null", "-"
    ]

    return cmd


def compute_ssim_command(video, reference_video, ssim_frames_file):
    cmd = [
        FFMPEG_COMMAND,
        "-nostdin",
        "-i", video,
        "-i", reference_video,
        "-lavfi",
        "ssim=" + ssim_frames_file,
        "-f", "null", "-"
    ]

    return cmd


def get_metadata_command(video):
    cmd = [
        FFPROBE_COMMAND,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video
    ]

    return cmd


def get_video_len(input_file):
    metadata = get_metadata_json(input_file)
    return meta.get_duration(metadata)


def filter_metric(cmd, regex, log_file):
    psnr = exec_cmd_to_string(cmd).splitlines()
    psnr = [line for line in psnr if re.search(regex, line)]

    with open(log_file, "w") as result_file:
        result_file.writelines(psnr)

    return psnr


def compute_psnr(video, reference_video, psnr_frames_file, psnr_log_file):
    cmd = compute_psnr_command(video, reference_video, psnr_frames_file)
    psnr = filter_metric(cmd, r'PSNR', psnr_log_file)

    return psnr


def compute_ssim(video, reference_video, ssim_frames_file, ssim_log_file):
    cmd = compute_ssim_command(video, reference_video, ssim_frames_file)
    ssim = filter_metric(cmd, r'SSIM', ssim_log_file)

    return ssim


def get_metadata(video, outputfile):
    cmd = get_metadata_command(video)
    exec_cmd_to_file(cmd, outputfile)


def get_metadata_str(video):
    cmd = get_metadata_command(video)
    return exec_cmd_to_string(cmd)


def get_metadata_json(video):
    cmd = get_metadata_command(video)
    metadata_str = exec_cmd_to_string(cmd)
    return json.loads(metadata_str)


def get_query_muxer_info_command(muxer: str) -> List[str]:
    cmd = [
        FFMPEG_COMMAND,
        '-nostdin',
        '-hide_banner',
        '-h', f'muxer={muxer}',
    ]
    return cmd


def _parse_default_audio_codec_out_of_muxer_info(muxer_info: str) -> List[str]:
    """
    Looks for audio codec in ffmpeg output.
    """

    # Sample of expected text passed to the regex:
    #
    # Muxer 3g2 [3GP2 (3GPP2 file format)]:
    #     Common extensions: 3g2.
    #     Default video codec: h263.
    #     Default audio codec: amr_nb.
    # matroska muxer AVOptions:
    return re.findall(
        r"""
        ^\s*                        # Leading whitespace
        Default\ ?audio\ ?codec:\ * # Label
        (.*[^\s.]|)\s*              # Codec name
        \.?                         # Optional dot at the end of the line
        \s*$                        # Trailing whitespace
        """,
        muxer_info,
        re.X | re.MULTILINE
    )


def query_muxer_info(muxer: str) -> Dict[str, Any]:
    """
    Returns information about a specific muxer, parsed out of the output of `ffmpeg -h`.

    Currently this includes the following fields (more may be added in the future):
    - `default_audio_codec`: the name of the audio codec ffmpeg uses when creating
        a video that uses this muxer and the name of the audio codec is not specified explicitly.
    """

    muxer_info_command = get_query_muxer_info_command(muxer)
    muxer_info = exec_cmd_to_string(muxer_info_command)

    audio_codecs = _parse_default_audio_codec_out_of_muxer_info(muxer_info)

    if len(audio_codecs) == 0:
        return {}

    if len(audio_codecs) >= 2:
        raise exceptions.NoMatchingEncoder(
            f"Found {len(audio_codecs)} things in ffmpeg output that could be the default audio codec name. "
            f"Expected exactly one.")

    return {
        'default_audio_codec': audio_codecs[0],
    }


def get_query_encoder_info_command(encoder: str) -> List[str]:
    return [
        FFMPEG_COMMAND,
        '-nostdin',
        '-hide_banner',
        '-h', f'encoder={encoder}',
    ]


def _parse_supported_sample_rates_out_of_encoder_info(codec_info):
    """
    Looks for supported sample rates in ffmpeg output.

    Currently this includes the following fields (more may be added in the future):
    - `sample_rates`: list of the sampling rates supported by the codec.
    """

    # Sample of expected text passed to the regex:
    #
    # Threading capabilities: none
    # Supported sample rates: 44100 48000 32000 22050 24000 16000 11025
    # Supported sample formats: s32p fltp s16p
    return re.findall(
        r"""
        ^\s*                           # Leading whitespace
        Supported\ ?sample\ ?rates:\ * # Label
        (.*[^\s]|)\s*$                 # Sample rate list
        """,
        codec_info,
        re.X | re.MULTILINE
    )


def query_encoder_info(encoder):
    ffmpeg_output = exec_cmd_to_string(get_query_encoder_info_command(encoder))
    matches = _parse_supported_sample_rates_out_of_encoder_info(ffmpeg_output)

    if len(matches) == 0:
        # We won't be able to validate target sample rate without this information
        print(f"WARNING: ffmpeg does not provide information about sample rates for encoder '{encoder}'.", file=sys.stderr)
        return {}

    if len(matches) >= 2:
        raise exceptions.InvalidSampleRateInfo(
            f"Found {len(matches)} things in ffmpeg output that could be the sample rate list for '{encoder}'. "
            f"Expected exactly one.")

    if len(matches) == 1:
        rate_strings = [s for s in matches[0].strip().split(" ") if s != '']
        try:
            return {'sample_rates': [int(s) for s in rate_strings]}
        except (ValueError, TypeError):
            raise exceptions.InvalidSampleRateInfo(f"Failed to parse sample rates reported by ffmpeg as integers.")

