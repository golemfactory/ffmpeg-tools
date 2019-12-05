import os
import tempfile
import shutil

from unittest import TestCase

from ffmpeg_tools import codecs
from ffmpeg_tools import commands
from ffmpeg_tools import formats
from ffmpeg_tools import meta


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
        for work_dir_id, work_dir_path in self.work_dirs.items():
            os.mkdir(work_dir_path)

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_extract_split_transcoding_merge_replace(self):
        num_segments = 3
        input_path = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        extract_step_output_path = os.path.join(self.work_dirs['extract'], "ForBiggerBlazes-[codec=h264][video-only].mp4")
        merge_step_output_path = os.path.join(self.work_dirs['merge'], "ForBiggerBlazes-[codec=h264][video-only]_TC.mkv")
        replace_step_output_path = os.path.join(self.work_dirs['replace'], "ForBiggerBlazes-[codec=h264]_TC.mkv")
        ffconcat_list_path = os.path.join(self.work_dirs['transcode'], "merge-input.ffconcat")

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

        with self.subTest(step='EXTRACT'):
            commands.extract_streams(
                input_path,
                extract_step_output_path,
                ['v'])

            self.assertTrue(os.path.isfile(extract_step_output_path))
            self.assertTrue(os.path.isfile(input_path))

        with self.subTest(step='SPLIT'):
            extract_step_output_metadata = commands.get_metadata_json(extract_step_output_path)
            extract_step_output_duration = meta.get_duration(extract_step_output_metadata)
            extract_step_output_demuxer = meta.get_format(extract_step_output_metadata)
            split_step_output_muxer = formats.get_safe_intermediate_format_for_demuxer(extract_step_output_demuxer)

            segment_list_path = commands.split_video(
                extract_step_output_path,
                self.work_dirs['split'],
                extract_step_output_duration / num_segments,
                split_step_output_muxer)

            self.assertTrue(os.path.isfile(extract_step_output_path))
            self.assertTrue(os.path.isfile(segment_list_path))

            with open(segment_list_path) as segment_list_file:
                segment_basenames = segment_list_file.read().splitlines()

            self.assertTrue(len(set(segment_basenames)), len(segment_basenames))
            for i, segment_basename in enumerate(segment_basenames):
                self.assertTrue(os.path.isfile(os.path.join(self.work_dirs['split'], segment_basename)))
                self.assertEqual(segment_basename, f"ForBiggerBlazes-[codec=h264][video-only]_{i}.mp4")

        for i, segment_basename in enumerate(segment_basenames):
            with self.subTest(step='TRANSCODE', segment_basename=segment_basename):
                segment_path = os.path.join(self.work_dirs['split'], segment_basename)
                transcoded_segment_path = os.path.join(
                    self.work_dirs['transcode'],
                    f"ForBiggerBlazes-[codec=h264][video-only]_{i}_TC.mkv")
                assert transcoded_segment_path != segment_path

                commands.transcode_video(
                    segment_path,
                    transcode_step_targs,
                    transcoded_segment_path)

                self.assertTrue(transcoded_segment_path.startswith(self.work_dirs['transcode']))
                self.assertTrue(os.path.isfile(transcoded_segment_path))
                self.assertTrue(os.path.isfile(segment_path))

        self.assertTrue(not os.path.exists(merge_step_output_path))

        with self.subTest(step='MERGE'):
            with open(ffconcat_list_path, 'w') as file:
                for i in range(len(segment_basenames)):
                    file.write(f"file 'ForBiggerBlazes-[codec=h264][video-only]_{i}_TC.mkv'\n")

            commands.merge_videos(
                ffconcat_list_path,
                merge_step_output_path,
                formats.Container.c_MATROSKA.value)

            self.assertTrue(os.path.isfile(merge_step_output_path))
            self.assertTrue(os.path.isfile(ffconcat_list_path))
            self.assertTrue(not os.path.exists(replace_step_output_path))

        with self.subTest(step='REPLACE'):
            commands.replace_streams(
                input_path,
                merge_step_output_path,
                replace_step_output_path,
                'v',
                replace_step_targs,
                formats.Container.c_MATROSKA.value)

            self.assertTrue(os.path.isfile(replace_step_output_path))
            self.assertTrue(os.path.isfile(merge_step_output_path))

        input_metadata               = commands.get_metadata_json(input_path)
        replace_step_output_metadata = commands.get_metadata_json(replace_step_output_path)

        self.assertEqual(meta.get_format(replace_step_output_metadata), formats.Container.c_MATROSKA_WEBM_DEMUXER.value)
        self.assertEqual(meta.get_video_codec(replace_step_output_metadata), codecs.VideoCodec.VP8.value)
        self.assertEqual(meta.get_resolution(replace_step_output_metadata), [200, 100])
        self.assertEqual(meta.get_frame_rate(replace_step_output_metadata), '25/1')
        self.assertEqual(meta.get_audio_codec(replace_step_output_metadata), codecs.AudioCodec.MP3.value)
        self.assertEqual(round(meta.get_duration(replace_step_output_metadata)), round(meta.get_duration(input_metadata)))
