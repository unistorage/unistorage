# -*- coding: utf-8 -*-
import re
import json
import os.path
import cPickle as pickle
from cStringIO import StringIO

import sh

import settings

try:
    with open(settings.AVCONV_DB_PATH) as f:
        avconv_db = pickle.load(f)
except:
    avconv_db = {}


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
    return {
        'width': parse_int(stream.get('width')),
        'height': parse_int(stream.get('height')),
        'codec': stream.get('codec_name'),
        'bitrate': stderr_data.get('video_bitrate'),
        'duration': parse_float(stream.get('duration')),
        'fps': parse_avg_frame_rate(stream.get('avg_frame_rate')),
    }


def extract_audio_data(stream, stderr_data):
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

    avprobe = sh.Command(settings.AVPROBE_BIN)
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


encoders = {
    'acodecs': {
        'vorbis': 'libvorbis',
        'amrnb': 'libopencore_amrnb',
        'mp3': 'libmp3lame'
    },
    'vcodecs': {
        'theora': 'libtheora',
        'h264': 'libx264',
        'divx': 'mpeg4',
        'vp8': 'libvpx',
        'h263': 'h263p',
        'mpeg1': 'mpeg1video',
        'mpeg2': 'mpeg2video'
    }
}


encoder_args = {
    'acodecs': {
        'aac': ['-strict', 'experimental']
    },
    'vcodecs': {
        'h263p': ['-threads', '1'],
        'libx264': ['-flags', '+loop', '-cmp', '+chroma', '-partitions',
                    '+parti4x4+partp8x8+partb8x8', '-subq', '5', '-trellis', '1', '-refs', '1',
                    '-coder', '0', '-me_range', '16', '-g', '300', '-keyint_min', '25',
                    '-sc_threshold', '40', '-i_qfactor', '0.71', '-rc_eq', "'blurCplx^(1-qComp)'",
                    '-qcomp', '0.6', '-qmin', '10', '-qmax', '51', '-qdiff', '4', '-level', '30']
    }
}


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
        encoder_name = encoders['acodecs'].get(codec, codec)
        args.extend(['-acodec', encoder_name])
        
        bitrate = audio_options.get('bitrate')
        if bitrate:
            args.extend(['-ab', str(bitrate)])
        sample_rate = audio_options.get('sample_rate')
        if sample_rate:
            args.extend(['-ar', str(sample_rate)])
        channels = audio_options.get('channels')
        if channels:
            args.extend(['-ac', str(channels)])
        args.extend(encoder_args['acodecs'].get(encoder_name, []))

    video_options = options.get('video')
    if video_options:
        codec = video_options['codec']
        encoder_name = encoders['vcodecs'].get(codec, codec)
        args.extend(['-vcodec', encoder_name])

        fps = video_options.get('fps')
        if fps:
            args.extend(['-r', str(fps)])
        bitrate = video_options.get('bitrate')
        if bitrate:
            args.extend(['-b', str(bitrate)])
        filters = video_options.get('filters')
        if filters:
            args.extend(['-vf', filters])
        args.extend(encoder_args['vcodecs'].get(encoder_name, []))

    format = options['format']
    avconv_format_name = format_aliases.get(format, format)
    args.extend(['-f', avconv_format_name])

    args = ['-i', source_fname] + args + ['-y', target_fname]
    avconv = sh.Command(settings.AVCONV_BIN)
    process = avconv(*args)
    process.wait()
    return process.exit_code


def get_codec_supported_actions(codec_type, codec_name):
    key = (codec_type == 'audio' and 'acodecs') or \
          (codec_type == 'video' and 'vcodecs')

    codec = avconv_db[key].get(codec_name)

    if codec_name in encoders[key]:
        encoder_name = encoders[key][codec_name]
        encoder = avconv_db[key].get(encoder_name)
        codec['encoding'] = codec['encoding'] or encoder['encoding']

    return codec
