import os
from typing import List, NamedTuple

from ffmpeg_tools import commands


def get_absolute_resource_path(filename: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resources',
        filename
    )


def make_parameterized_test_name_generator_for_scalar_values(scalar_names: List[str]):
    def test_case_name_generator(testcase_func, param_num, param):
        assert len(param[0]) == len(scalar_names)

        scalar_values = [str(value) for value in param[0]]
        parameter_names_and_values = '_'.join(commands.flatten_list(zip(scalar_names, scalar_values)))

        return f'{testcase_func.__name__}_{param_num}_{parameter_names_and_values}'

    return test_case_name_generator


class SampleStreamSource(NamedTuple):
    source_video_path: str  # File containing the stream
    stream_index: int       # Index of the stream that either has the right
                            # type or can be converted to it


SAMPLE_STREAM_SOURCES = {
    # NOTE: This list is incomplete and only has definitions for codecs that
    # were actually needed in existing tests. Feel free to add more as needed.
    'h264': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 0),
    'mjpeg': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 0),
    'flv1': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 0),
    'vp8': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 0),
    'aac': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 1),
    'mp3': SampleStreamSource('ForBiggerBlazes-[codec=h264].mp4', 1),
    'subrip': SampleStreamSource('sample.srt', 0),
    'ass': SampleStreamSource('sample.srt', 0),
    'webvtt': SampleStreamSource('sample.srt', 0),
    'mov_text': SampleStreamSource('sample.srt', 0),
}


def generate_sample_video_command(
    streams: List[str],
    output_path: str,
    container: str,
) -> str:
    assert set(streams).issubset(set(SAMPLE_STREAM_SOURCES))

    selected_sources = [(codec_name, SAMPLE_STREAM_SOURCES[codec_name]) for codec_name in streams]
    input_files = [source.source_video_path for codec_name, source in selected_sources]
    unique_input_files = dict.fromkeys(input_files).keys()
    input_output_map = {input_file: i for i, input_file in enumerate(unique_input_files)}

    command_and_global_options = [
        commands.FFMPEG_COMMAND,
        "-nostdin",
    ]
    input_options = commands.flatten_list([
        ["-i", get_absolute_resource_path(input_file)]
        for input_file in unique_input_files
    ])
    codec_options = commands.flatten_list([
        # TODO: This code works for the current selection of codecs but in
        # general it would be better to rely on encoder rather than codec names.
        # TODO: Consider optimizing it by using `-codec copy` when the stream
        # already uses the right codec.
        [
            "-map", f"{input_output_map[source.source_video_path]}:{source.stream_index}",
            f"-codec:{output_stream_index}", codec_name,
        ] for output_stream_index, (codec_name, source) in enumerate(selected_sources)
    ])
    output_options = [
        "-f", container,
        output_path,
    ]

    return (
        command_and_global_options +
        input_options +
        codec_options +
        output_options
    )


def generate_sample_video(*args, **kwargs) -> None:
    """
    Generates a franken-file with desired stream count, types and codecs by
    combining the resource files we have in the repository. Converts the input
    streams to the right codec if the desired type is not already available.

    This is meant for uses where the content does not really matter and we
    really only need a video with the right structure - e.g. integration tests.
    """
    commands.exec_cmd(generate_sample_video_command(*args, **kwargs))
