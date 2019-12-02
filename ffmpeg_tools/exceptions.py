class NoMatchingEncoder(Exception):
    pass


class CommandFailed(Exception):
    def __init__(self, command, error_code):
        super().__init__()
        self.command = command
        self.error_code = error_code


class InvalidArgument(Exception):
    pass


class InvalidCommandOutput(Exception):
    pass


class FileAlreadyExists(Exception):
    pass


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
