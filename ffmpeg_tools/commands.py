import os
import re
import subprocess
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


def get_lists_of_unsupported_stream_numbers(
    metadata,
):
    unsupported_data_streams = []
    unsupported_subtitle_streams = []
    for stream_metadata in metadata.get('streams'):
        if (
            stream_metadata.get('codec_type') == 'data' and
            stream_metadata.get('codec_name') not in
            codecs.DATA_STREAM_WHITELIST
        ):
            unsupported_data_streams.append(stream_metadata.get('index'))

        elif (
            stream_metadata.get('codec_type') == 'subtitle' and
            stream_metadata.get('codec_name') not in
            codecs.SUBTITLE_STREAM_WHITELIST
        ):
            unsupported_subtitle_streams.append(stream_metadata.get('index'))

    return (unsupported_data_streams, unsupported_subtitle_streams)


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
    :param targs: Dictionary with additional parameters used by command
    :param container: Container of output file
        See https://ffmpeg.org/ffmpeg.html#Stream-specifiers.
        The following values are supported:
            - `v` - same as `V`.
            - `V` - video streams which are not attached pictures, video
                    thumbnails or cover arts.
            - `a` - audio streams.
            - `s` - subtitle streams.
            - `d` - data streams.
            - `t` - attachments.
    """
    VALID_STREAM_TYPES = {'v', 'V', 'a', 's', 'd', 't'}
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

    metadata = get_metadata_json(input_file)
    (unsupported_data_streams, unsupported_subtitle_streams) = \
        get_lists_of_unsupported_stream_numbers(metadata)

    data_map_options = []
    subtitle_map_options = []
    if strip_unsupported_data_streams:
        data_map_options = (
            ["-map", f"-0:{index}"]
            for index in unsupported_data_streams
        )
    if strip_unsupported_subtitle_streams:
        subtitle_map_options = (
            ["-map", f"-0:{index}"]
            for index in unsupported_subtitle_streams
        )

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
        "-copy_unknown",
        "-c:v", "copy",
        "-c:d", "copy",
    ] + ([
        "-f", container,
    ] if container is not None else []) + ([
        "-c:a", codecs.get_audio_encoder(targs['audio']['codec']),
    ] if 'audio' in targs and 'codec' in targs['audio'] else []) + ([
        "-b:a", targs['audio']['bitrate'],
    ] if 'audio' in targs and 'bitrate' in targs['audio'] else []) + [
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
        Default\ ?audio\ ?codec:\s* # Label
        (.*[^\s.])\s*               # Codec name
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
