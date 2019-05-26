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

    def test_transcoding_should_preserve_bitrate(self):
        params = ffmpeg.meta.create_params("mkv", [640, 400], "mpeg4")
        assert 'bitrate' not in params.get("video", {})

        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        output_video = os.path.join(tempfile.gettempdir(), "ForBiggerBlazes-[codec=h264].mp4")

        if os.path.exists(output_video):
            os.remove(output_video)

        ffmpeg.commands.transcode_video(input_video, params, output_video, use_playlist=False)
        self.assertTrue(os.path.exists(output_video))

        input_bitrate_strings = ffmpeg.meta.get_video_bitrates(ffmpeg.meta.get_metadata(input_video))
        output_bitrate_strings = ffmpeg.meta.get_video_bitrates(ffmpeg.meta.get_metadata(output_video))
        assert len(input_bitrate_strings) == 1 and len(output_bitrate_strings) == 1

        input_bitrate = int(input_bitrate_strings[0])
        output_bitrate = int(output_bitrate_strings[0])

        # FIXME: I'm accepting a 10% difference as a match here but from my limited
        # experiments I've seen that you can't reliably get the bitrate you want.
        # The result often varies (sometimes only a little, sometimes a lot) from what you request.
        self.assertAlmostEqual(output_bitrate, input_bitrate, delta=input_bitrate * 0.10)

    def test_transcoding_should_not_preserve_bitrate_if_set_to_none(self):
        # NOTE: There's no way to get a structure like this from create_params().
        # It treats None the same way as a missing keys.
        params = {
            "format": "mkv",
            "video": {
                "codec": "mpeg4",
                "bitrate": None,
            }
        }
        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        output_video = os.path.join(tempfile.gettempdir(), "ForBiggerBlazes-[codec=h264].mp4")

        if os.path.exists(output_video):
            os.remove(output_video)

        ffmpeg.commands.transcode_video(input_video, params, output_video, use_playlist=False)
        self.assertTrue(os.path.exists(output_video))

        input_bitrate_strings = ffmpeg.meta.get_video_bitrates(ffmpeg.meta.get_metadata(input_video))
        output_bitrate_strings = ffmpeg.meta.get_video_bitrates(ffmpeg.meta.get_metadata(output_video))
        assert len(input_bitrate_strings) == 1 and len(output_bitrate_strings) == 1

        input_bitrate = int(input_bitrate_strings[0])
        output_bitrate = int(output_bitrate_strings[0])

        self.assertNotAlmostEqual(output_bitrate, input_bitrate, delta=input_bitrate * 0.15)

    def test_get_video_length(self):
        input_video = "tests/resources/ForBiggerBlazes-[codec=h264].mp4"
        length = ffmpeg.commands.get_video_len(input_video)

        assert length == 15.021667


    def test_failed_command(self):
        with self.assertRaises(ffmpeg.commands.CommandFailed):
            ffmpeg.commands.get_video_len("bla")
