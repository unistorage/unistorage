# -*- coding: utf-8 -*-
import re
import json
import os.path
from cStringIO import StringIO

import sh


def parse_float(val):
    try:
        return float(val)
    except:
        return None


def parse_int(val):
    try:
        return int(val)
    except:
        return None


def extract_video_data(stream, stderr_data):
    def parse_avg_frame_rate(val):
        if '/' in val:
            n, d = map(parse_float, val.split('/'))
            return n and d and n / d
        elif '.' in val:
            return parse_float(val)
    stream.setdefault(None)
    stderr_data.setdefault(None)
    return {
        'width': parse_int(stream.get('width')),
        'height': parse_int(stream.get('height')),
        'codec': stream.get('codec_name'),
        'bitrate': stderr_data.get('video_bitrate'),
        'duration': parse_float(stream.get('duration')),
        'fps': parse_avg_frame_rate(stream.get('avg_frame_rate')),
    }


def extract_audio_data(stream, stderr_data):
    stream.setdefault(None)
    stderr_data.setdefault(None)
    return {
        'channels': parse_int(stream.get('channels')),
        'sample_rate': parse_float(stream.get('sample_rate')),
        'codec': stream.get('codec_name'),
        'bitrate': stderr_data.get('audio_bitrate'),
        'duration': parse_float(stream.get('duration'))
    }


def parse_stdout(stdout):
    return json.loads(stdout)


def parse_stderr(stderr):
    data = {}
    regexp = r'Stream.*(?P<stream_type>Audio|Video):.*?(?P<bitrate>\d+) kb/s'
    for match in re.finditer(regexp, stderr):
        stream_type = match.group('stream_type').lower()
        key = '%s_bitrate' % stream_type
        data[key] = '%dk' % int(match.group('bitrate'))
    return data


def avprobe(fname):
    stderr = StringIO()
    stdout = StringIO()

    avprobe = sh.Command('/usr/bin/avprobe')
    process = avprobe('-print_format', 'json', '-show_format', '-show_streams',
                      fname, _out=stdout, _err=stderr)
    process.wait()
    
    stdout_data = parse_stdout(stdout.getvalue())
    stderr_data = parse_stderr(stderr.getvalue())

    formats = stdout_data['format']['format_name'].split(',')
    extension = None
    if '.' in fname:
        extension = os.path.splitext(fname)[1][1:]
    format = extension in formats and extension or formats[0]

    video = None
    audio = None
    for stream in stdout_data['streams']:
        if stream['codec_type'] == 'video' and not video:
            video = extract_video_data(stream, stderr_data)
        elif stream['codec_type'] == 'audio' and not audio:
            audio = extract_audio_data(stream, stderr_data)

    return {
        'video': video,
        'audio': audio,
        'format': format
    }


acodec_encoders = {
    'vorbis': 'libvorbis',
    'amrnb': 'libopencore_amrnb',
    'mp3': 'libmp3lame'
}

acodecs_additional_args = {
    'aac': ['-strict', 'experimental']
}

vcodec_encoders = {
    'theora': 'libtheora',
    'h264': 'libx264',
    'divx': 'mpeg4',
    'vp8': 'libvpx',
    'h263': 'h263p',
    'mpeg1': 'mpeg1video',
    'mpeg2': 'mpeg2video'
}

vcodecs_additional_args = {
    'h263': ['-threads', '1'],
    'h264':  '-flags +loop -cmp +chroma '
             '-partitions +parti4x4+partp8x8+partb8x8 -subq 5 -trellis 1 '
             '-refs 1 -coder 0 -me_range 16 -g 300 -keyint_min 25 '
             '-sc_threshold 40 -i_qfactor 0.71 -rc_eq \'blurCplx^(1-qComp)\' '
             '-qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -level 30'.split()
}
# TODO additional args for aliases?

format_aliases = {
    'mpeg': 'mpegts',
    'mpg': 'mpegts',
    'mkv': 'matroska'
}

def avconv(source_fname, target_fname, options):
    args = []

    audio_options = options.get('audio')
    if audio_options:
        codec = audio_options['codec']
        bitrate = audio_options.get('bitrate')
        sample_rate = audio_options.get('sample_rate')
        channels = audio_options.get('channels')
        
        avconv_codec_name = acodec_encoders.get(codec, codec) 
        args.extend(['-acodec', avconv_codec_name])
        if bitrate:
            args.extend(['-ab', str(bitrate)])
        if sample_rate:
            args.extend(['-ar', str(sample_rate)])
        if channels:
            args.extend(['-ac', str(channels)])
        additional_args = acodecs_additional_args.get(codec, [])
        args.extend(additional_args)

    video_options = options.get('video')
    if video_options:
        codec = video_options['codec']
        bitrate = video_options.get('bitrate')
        fps = video_options.get('fps')
        filters = video_options.get('filters')

        avconv_codec_name = vcodec_encoders.get(codec, codec)
        args.extend(['-vcodec', avconv_codec_name])
        if fps:
            args.extend(['-r', str(fps)])
        if bitrate:
            args.extend(['-b', str(bitrate)])
        if filters:
            args.extend(['-vf', filters])
        additional_args = vcodecs_additional_args.get(codec, [])
        args.extend(additional_args)

    format = options['format']
    avconv_format_name = format_aliases.get(format, format)
    args.extend(['-f', avconv_format_name])

    args = ['-i', source_fname] + args + ['-y', target_fname]
    avconv = sh.Command('/usr/bin/avconv')
    process = avconv(*args)
    process.wait()
    return process.exit_code
