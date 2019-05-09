import os
import re
import subprocess

from io import StringIO
import codecs


FFMPEG_COMMAND = "ffmpeg"
FFPROBE_COMMAND = "ffprobe"

TMP_DIR = "/golem/work/tmp/"




def exec_cmd(cmd, file=None):
    print("Executing command:")
    print(cmd)

    pc = subprocess.Popen(cmd, stdout=file, stderr=file)

    ret = pc.wait()
    if ret != 0:
        exit(ret)
    return ret


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
        exit(result.returncode)
    return result.stdout.decode('utf-8')


def split_video(input_file, output_dir, split_len):
    [_, filename] = os.path.split(input_file)
    [basename, _] = os.path.splitext(filename)

    output_list_file = os.path.join(output_dir, basename + "_.m3u8")

    split_list_file = split(input_file, output_list_file, split_len)

    return split_list_file


def split(input, output_list_file, segment_time):
    cmd, file_list = split_video_command(input, output_list_file,
                                         segment_time)
    exec_cmd(cmd)

    return file_list


def split_video_command(input, output_list_file, segment_time):
    cmd = [FFMPEG_COMMAND,
           "-i", input,
           "-hls_time", "{}".format(segment_time),
           "-hls_list_size", "0",
           "-c", "copy",
           "-mpegts_copyts", "1",
           output_list_file
           ]

    return cmd, output_list_file


def transcode_video(track, targs, output, use_playlist):
    cmd = transcode_video_command(track, output,
                                  targs, use_playlist)
    return exec_cmd(cmd)


def transcode_video_command(track, output_playlist_name, targs, use_playlist):
    cmd = [FFMPEG_COMMAND,
           # process an input file
           "-i",
           # input file
           "{}".format(track)
           ]

    if use_playlist:
        playlist_cmd = [
            # It states that all entries from list should be processed
            "-hls_list_size", "0",
            "-copyts"
        ]
        cmd.extend(playlist_cmd)

    # video settings
    try:
        vcodec = targs['video']['codec']
        cmd.append("-c:v")
        cmd.append(codecs.get_video_encoder(vcodec))
    except:
        pass
    try:
        fps = str(targs['frame_rate'])
        cmd.append("-r")
        cmd.append(fps)
    except:
        pass
    try:
        vbitrate = targs['video']['bitrate']
        cmd.append("-b:v")
        cmd.append(vbitrate)
    except:
        pass
    # audio settings
    try:
        acodec = targs['audio']['codec']
        cmd.append("-c:a")
        cmd.append(codecs.get_audio_encoder(acodec))
    except:
        pass
    try:
        abitrate = targs['audio']['bitrate']
        cmd.append("-c:a")
        cmd.append(abitrate)
    except:
        pass
    try:
        res = targs['resolution']
        cmd.append("-vf")
        cmd.append("scale={}:{}".format(res[0], res[1]))
    except:
        pass
    try:
        scale = targs["scaling_alg"]
        cmd.append("-sws_flags")
        cmd.append("{}".format(scale))
    except:
        pass

    cmd.append("{}".format(output_playlist_name))

    return cmd


def merge_videos(input_files, output):
    cmd, list_file = merge_videos_command(input_files, output)
    exec_cmd(cmd)


def merge_videos_command(input_file, output):
    cmd = [FFMPEG_COMMAND,
           "-i", input_file,
           "-c", "copy",
           "-mpegts_copyts", "1",
           output
           ]

    return cmd, input_file


def get_video_len_command(input_file):
    cmd = [FFPROBE_COMMAND,
           "-v", "error",
           "-select_streams", "v:0",
           "-show_entries", "stream=duration",
           "-of", "default=noprint_wrappers=1:nokey=1",
           input_file
           ]

    return cmd


def get_video_len(input_file):
    cmd = get_video_len_command(input_file)
    result = exec_cmd_to_string(cmd)

    return float(result)


def compute_psnr_command(video, reference_video, psnr_frames_file):
    cmd = [FFMPEG_COMMAND,
           "-i", video,
           "-i", reference_video,
           "-lavfi",
           "psnr=" + psnr_frames_file,
           "-f", "null", "-"
           ]

    return cmd


def compute_ssim_command(video, reference_video, ssim_frames_file):
    cmd = [FFMPEG_COMMAND,
           "-i", video,
           "-i", reference_video,
           "-lavfi",
           "ssim=" + ssim_frames_file,
           "-f", "null", "-"
           ]

    return cmd


def get_metadata_command(video):
    cmd = [FFPROBE_COMMAND,
           "-v", "quiet",
           "-print_format", "json",
           "-show_format",
           "-show_streams",
           video
           ]

    return cmd


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