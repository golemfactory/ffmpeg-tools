import os
import tempfile

from unittest import TestCase
import ffmpeg_tools as ffmpeg


class TestCommands(TestCase):

    def test_transcoding(self):
        params = ffmpeg.meta.create_params("mp4", [1280, 800], "h265")

        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        output_video = os.path.join(tempfile.gettempdir(), "ForBiggerBlazes-[codec=h265].mp4")
        
        if os.path.exists(output_video):
            os.remove(output_video)

        ffmpeg.commands.transcode_video(input_video, params, output_video, False)

        assert os.path.exists(output_video)


    def test_get_video_length(self):
        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        length = ffmpeg.commands.get_video_len(input_video)

        assert length == 15.021667


    def test_failed_command(self):
        with self.assertRaises(ffmpeg.commands.CommandFailed):
            ffmpeg.commands.get_video_len("bla")
