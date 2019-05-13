import os
import re
import subprocess
import json

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
           "-nostdin",
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
           "-nostdin",
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
    if 'video' in targs and 'codec' in targs['video']:
        vcodec = targs['video']['codec']
        cmd.append("-c:v")
        cmd.append(codecs.get_video_encoder(vcodec))

    if 'frame_rate' in targs:
        fps = str(targs['frame_rate'])
        cmd.append("-r")
        cmd.append(fps)

    if 'video' in targs and 'bitrate' in targs['video']:
        vbitrate = targs['video']['bitrate']
        cmd.append("-b:v")
        cmd.append(vbitrate)

    # audio settings
    if 'audio' in targs and 'codec' in targs['audio']:
        acodec = targs['audio']['codec']
        cmd.append("-c:a")
        cmd.append(codecs.get_audio_encoder(acodec))

    if 'audio' in targs and 'bitrate' in targs['audio']:
        abitrate = targs['audio']['bitrate']
        cmd.append("-b:a")
        cmd.append(abitrate)

    if 'resolution' in targs:
        res = targs['resolution']
        cmd.append("-vf")
        cmd.append("scale={}:{}".format(res[0], res[1]))

    if 'scaling_alg' in targs:
        scale = targs["scaling_alg"]
        cmd.append("-sws_flags")
        cmd.append("{}".format(scale))

    cmd.append("{}".format(output_playlist_name))

    return cmd


def merge_videos(input_files, output):
    cmd, list_file = merge_videos_command(input_files, output)
    exec_cmd(cmd)


def merge_videos_command(input_file, output):
    cmd = [FFMPEG_COMMAND,
           "-nostdin",
           "-i", input_file,
           "-c", "copy",
           "-mpegts_copyts", "1",
           output
          ]

    return cmd, input_file


def compute_psnr_command(video, reference_video, psnr_frames_file):
    cmd = [FFMPEG_COMMAND,
           "-nostdin",
           "-i", video,
           "-i", reference_video,
           "-lavfi",
           "psnr=" + psnr_frames_file,
           "-f", "null", "-"
          ]

    return cmd


def compute_psnr_command(video, reference_video, psnr_frames_file):
    cmd = [FFMPEG_COMMAND,
           "-nostdin",
           "-i", video,
           "-i", reference_video,
           "-lavfi",
           "psnr=" + psnr_frames_file,
           "-f", "null", "-"
          ]

    return cmd


def compute_ssim_command(video, reference_video, ssim_frames_file):
    cmd = [FFMPEG_COMMAND,
           "-nostdin",
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


def get_video_len(input_file):
    cmd = get_metadata_command(input_file)
    result = exec_cmd_to_string(cmd)

    # result should be json
    metadata = json.loads(result)
    format_meta = metadata["format"]

    return float(format_meta["duration"])


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