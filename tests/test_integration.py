import os
import tempfile
import shutil
from unittest import TestCase

from ffmpeg_tools import codecs
from ffmpeg_tools import commands
from ffmpeg_tools import formats
from ffmpeg_tools import meta
from tests.utils import get_absolute_resource_path, generate_sample_video


class TestIntegration(TestCase):

    def setUp(self):
        self.tmp_dir = os.path.join(tempfile.mkdtemp(prefix='ffmpeg-tools-integration-test-'))
        self.work_dirs = {
            'extract': os.path.join(self.tmp_dir, 'extract'),
            'split': os.path.join(self.tmp_dir, 'split'),
            'transcode': os.path.join(self.tmp_dir, 'transcode'),
            'merge': os.path.join(self.tmp_dir, 'merge'),
            'replace': os.path.join(self.tmp_dir, 'replace'),
        }
        for _, work_dir_path in self.work_dirs.items():
            os.mkdir(work_dir_path)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def run_extract_step(self, input_path, output_path):
        commands.extract_streams(
            input_path,
            output_path,
            ['v'])

    def run_split_step(self, input_path, work_dir, num_segments):
        input_metadata = commands.get_metadata_json(input_path)
        input_duration = meta.get_duration(input_metadata)
        input_demuxer = meta.get_format(input_metadata)
        output_muxer = formats.get_safe_intermediate_format_for_demuxer(input_demuxer)

        segment_list_path = commands.split_video(
            input_path,
            work_dir,
            input_duration / num_segments,
            output_muxer)

        return segment_list_path

    def run_transcode_step(self, segment_path, transcoded_segment_path, transcode_step_targs):
        assert transcoded_segment_path != segment_path

        commands.transcode_video(
            segment_path,
            transcode_step_targs,
            transcoded_segment_path)

    def run_extract_split_transcoding_merge_replace_test(
        self,
        num_segments,
        input_path,
        extract_step_output_path,
        split_step_basename_template,
        transcode_step_basename_template,
        merge_step_output_path,
        replace_step_output_path,
        ffconcat_list_path,
        transcode_step_targs,
        replace_step_targs,
    ):
        with self.subTest(step='EXTRACT'):
            self.run_extract_step(input_path, extract_step_output_path)
            self.assert_extract_step_successful(input_path, extract_step_output_path)

        with self.subTest(step='SPLIT'):
            segment_list_path = self.run_split_step(extract_step_output_path, self.work_dirs['split'], num_segments)

            self.assert_split_step_successful(extract_step_output_path, segment_list_path)
            segment_basenames = self.read_segment_basenames(segment_list_path)
            self.assert_segments_correct(segment_basenames, self.work_dirs['split'], split_step_basename_template)

        for i, segment_basename in enumerate(segment_basenames):
            with self.subTest(step='TRANSCODE', segment_basename=segment_basename):
                segment_path = os.path.join(self.work_dirs['split'], segment_basename)
                transcoded_segment_path = os.path.join(
                    self.work_dirs['transcode'],
                    transcode_step_basename_template.format(i))

                self.run_transcode_step(segment_path, transcoded_segment_path, transcode_step_targs)
                self.assert_transcoding_step_successful(segment_path, transcoded_segment_path, self.work_dirs['transcode'])

        self.assertTrue(not os.path.exists(merge_step_output_path))

        with self.subTest(step='MERGE'):
            self.create_ffconcat_list_file(segment_basenames, ffconcat_list_path, transcode_step_basename_template)
            commands.merge_videos(ffconcat_list_path, merge_step_output_path, formats.Container.c_MATROSKA.value)

            self.assert_merge_step_successful(merge_step_output_path, ffconcat_list_path)

        with self.subTest(step='REPLACE'):
            commands.replace_streams(
                input_path,
                merge_step_output_path,
                replace_step_output_path,
                'v',
                replace_step_targs,
                formats.Container.c_MATROSKA.value)

            self.assert_replace_step_successful(merge_step_output_path, replace_step_output_path)

        self.assert_video_metadata(replace_step_output_path, transcode_step_targs, replace_step_targs)
        self.assert_same_video_duration(input_path, replace_step_output_path)

    def create_ffconcat_list_file(self, segment_basenames, ffconcat_list_path, segment_basename_template):
        with open(ffconcat_list_path, 'w') as file:
            for i in range(len(segment_basenames)):
                segment_basename = segment_basename_template.format(i)
                file.write(f"file '{segment_basename}'\n")

    def read_segment_basenames(self, segment_list_path):
        with open(segment_list_path) as segment_list_file:
            return segment_list_file.read().splitlines()

    def assert_extract_step_successful(self, input_path, output_path):
        self.assertTrue(os.path.isfile(input_path))
        self.assertTrue(os.path.isfile(output_path))

    def assert_split_step_successful(self, input_path, segment_list_path):
        self.assertTrue(os.path.isfile(input_path))
        self.assertTrue(os.path.isfile(segment_list_path))

    def assert_segments_correct(self, segment_basenames, work_dir, segment_name_template):
        self.assertTrue(len(set(segment_basenames)), len(segment_basenames))

        for i, segment_basename in enumerate(segment_basenames):
            self.assertTrue(os.path.isfile(os.path.join(work_dir, segment_basename)))
            self.assertEqual(segment_basename, segment_name_template.format(i))

    def assert_transcoding_step_successful(self, segment_path, transcoded_segment_path, work_dir):
        self.assertTrue(transcoded_segment_path.startswith(work_dir))
        self.assertTrue(os.path.isfile(transcoded_segment_path))
        self.assertTrue(os.path.isfile(segment_path))

    def assert_merge_step_successful(self, output_path, ffconcat_list_path):
        self.assertTrue(os.path.isfile(output_path))
        self.assertTrue(os.path.isfile(ffconcat_list_path))

    def assert_replace_step_successful(self, input_path, output_path):
        self.assertTrue(os.path.isfile(input_path))
        self.assertTrue(os.path.isfile(output_path))

    def assert_video_metadata(
        self,
        video_path,
        transcode_step_targs,
        replace_step_targs,
    ):
        metadata = commands.get_metadata_json(video_path)

        num_video_streams = meta.count_streams(metadata, 'video')
        num_audio_streams = meta.count_streams(metadata, 'audio')

        expected_demuxer = formats.Container(transcode_step_targs['container']).get_demuxer()
        self.assertEqual(meta.get_format(metadata), expected_demuxer)
        self.assertEqual(meta.get_codecs(metadata, 'video'), [transcode_step_targs['video']['codec']] * num_video_streams)
        self.assertEqual(meta.get_resolutions(metadata), [transcode_step_targs['resolution']] * num_video_streams)
        self.assertEqual(meta.get_frame_rates(metadata), [transcode_step_targs['frame_rate']] * num_video_streams)
        self.assertEqual(meta.get_codecs(metadata, 'audio'), [replace_step_targs['audio']['codec']] * num_audio_streams)

    def assert_same_video_duration(self, source_video_path, transcoded_video_path):
        source_metadata = commands.get_metadata_json(source_video_path)
        transcoded_metadata = commands.get_metadata_json(transcoded_video_path)

        self.assertEqual(round(meta.get_duration(transcoded_metadata)), round(meta.get_duration(source_metadata)))

    def test_extract_split_transcoding_merge_replace(self):
        transcode_step_targs = {
            'container': formats.Container.c_MATROSKA.value,
            'frame_rate': '25/1',
            'video': {
                'codec': codecs.VideoCodec.VP8.value,
                'bitrate': '1000k',
            },
            'resolution': [200, 100],
            'scaling_alg': 'neighbor',
        }
        replace_step_targs = {
            'audio': {
                'codec': codecs.AudioCodec.MP3.value,
                'bitrate': '128k',
            },
        }

        self.run_extract_split_transcoding_merge_replace_test(
            num_segments=3,
            input_path=get_absolute_resource_path("ForBiggerBlazes-[codec=h264].mp4"),
            extract_step_output_path=os.path.join(self.work_dirs['extract'], "ForBiggerBlazes-[codec=h264][video-only].mp4"),
            split_step_basename_template="ForBiggerBlazes-[codec=h264][video-only]_{}.mp4",
            transcode_step_basename_template="ForBiggerBlazes-[codec=h264][video-only]_{}_TC.mkv",
            merge_step_output_path=os.path.join(self.work_dirs['merge'], "ForBiggerBlazes-[codec=h264][video-only]_TC.mkv"),
            replace_step_output_path=os.path.join(self.work_dirs['replace'], "ForBiggerBlazes-[codec=h264]_TC.mkv"),
            ffconcat_list_path=os.path.join(self.work_dirs['transcode'], "merge-input.ffconcat"),
            transcode_step_targs=transcode_step_targs,
            replace_step_targs=replace_step_targs,
        )

    def test_replace_streams_converts_subtitles(self):
        input_path = os.path.join(self.tmp_dir, 'input.mkv')
        replacement_path = get_absolute_resource_path("ForBiggerBlazes-[codec=h264].mp4")
        output_path = os.path.join(self.tmp_dir, 'output.mp4')
        generate_sample_video(
            [
                codecs.SubtitleCodec.ASS.value,
                codecs.VideoCodec.MJPEG.value,
                codecs.AudioCodec.MP3.value,
                codecs.SubtitleCodec.SUBRIP.value,
                codecs.VideoCodec.FLV1.value,
                codecs.AudioCodec.AAC.value,
                codecs.SubtitleCodec.WEBVTT.value,
            ],
            input_path,
            container=formats.Container.c_MATROSKA.value)

        assert os.path.isfile(input_path)
        assert not os.path.isfile(output_path)

        commands.replace_streams(
            input_path,
            replacement_path,
            output_path,
            stream_type='v',
            targs={},
            container=formats.Container.c_MP4.value,
            strip_unsupported_data_streams=True,
            strip_unsupported_subtitle_streams=True,
        )

        self.assertTrue(os.path.isfile(output_path))

        metadata = meta.get_metadata(output_path)
        self.assertEqual(meta.get_format(metadata), formats.Container.c_QUICK_TIME_DEMUXER.value)
        self.assertIn('streams', metadata)

        expected_streams = [
             ('video', codecs.VideoCodec.H_264.value),
             ('subtitle', codecs.SubtitleCodec.MOV_TEXT.value),
             ('audio', codecs.AudioCodec.AAC.value),
             ('subtitle', codecs.SubtitleCodec.MOV_TEXT.value),
             ('audio', codecs.AudioCodec.AAC.value),
             ('subtitle', codecs.SubtitleCodec.MOV_TEXT.value),
        ]
        streams = [
            (stream_metadata.get('codec_type'), stream_metadata.get('codec_name'))
            for stream_metadata in metadata['streams']
        ]
        self.assertEqual(streams, expected_streams)
