# -*- coding: utf-8 -*-
import re
import json
import os.path
import subprocess
import cPickle as pickle
from StringIO import StringIO

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
    """Парсит сырые данные, полученные от ffmpeg. Возвращает только нужные поля,
    приведённые к своим типам -- словарь, удовлетворяющий следующей схеме:
    ```
    {
        'width': int,
        'height': int,
        'codec': string,  # имя кодека в терминологии ffmpeg
        'bitrate': string,  # битрейт в формате "%dk", например, "256k"
        'duration': float,  # длительность видео в секундах
        'fps': float,  # frame per second

    }
    ```

    :param stream: словарь, содержащий данные о потоке из stdout-а ffmpeg
    :param stderr_data: словарь, содержащие данные из stderr-а ffmpeg
    """
    def parse_avg_frame_rate(val):
        """Парсит FPS в ffmpeg-овском формате. Возвращает в виде float."""
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
    """Парсит сырые данные, полученные от ffmpeg. Возвращает только нужные поля,
    приведённые к своим типам -- словарь, удовлетворяющий следующей схеме:
    ```
    {
        'channels': int,  # количество каналов
        'sample_rate': float,
        'codec': string,  # имя кодека в терминологии ffmpeg
        'bitrate': string,  # битрейт в формате "%dk", например, "256k"
        'duration': float,  # длительность видео в секундах
    }
    ```

    :param stream: словарь, содержащий данные о потоке из stdout-а ffmpeg
    :param stderr_data: словарь, содержащие данные из stderr-а ffmpeg
    """
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
    """Парсит stderr ffmpeg-а и извлекает из него битрейты первых встреченных
    аудио- и видеопотоков (ffmpeg выдаёт эти данные _только_ в stderr).
    Возвращает словарь, удовлетворяющий следующей схеме:
    ```
    {
        'audio_bitrate': string or None,  # битрейт в формате "%dk", например, "256k"
        'video_bitrate': string or None
    }
    """
    data = {
        'audio_bitrate': None,
        'video_bitrate': None
    }
    regexp = r'Stream.*(?P<stream_type>Audio|Video):.*?(?P<bitrate>\d+) kb/s'
    for match in re.finditer(regexp, stderr):
        stream_type = match.group('stream_type').lower()
        key = '%s_bitrate' % stream_type
        data[key] = '%dk' % int(match.group('bitrate'))

    regexp = r'Stream.*Video:.*?\s(?P<size>\d+x\d+)(?:,|\n)'
    match = re.search(regexp, stderr)
    if match:
        data['video_size'] = match.group('size')
    return data


def get_extension(fname):
    extension = None
    if '.' in fname:
        _, extension = os.path.splitext(fname)
    return extension and extension.lstrip('.')


def apply_hacks(result, stdout_data, stderr_data):
    video = result['video']
    audio = result['audio']

    if not video:
        return result
    
    if video['codec'] == 'vp6f':
        # 1. Битрейт и длительность находятся в секции format
        format_data = stdout_data['format']
        bitrate = format_data.get('bit_rate')
        if bitrate and not video['bitrate']:
            result['video']['bitrate'] = '%ik' % (parse_float(bitrate) / 1000)

        duration = format_data.get('duration')
        if duration and not video['duration']:
            result['video']['duration'] = parse_float(duration)

        # 2. Верные размеры видео выводятся в stderr
        width, height = map(int, stderr_data['video_size'].split('x'))
        result['video'].update({
            'width': width,
            'height': height
        })

        # 3. Аудио не имеет длительности
        if not audio['duration']:
            audio['duration'] = result['video']['duration']

        # 4. FPS и вовсе нигде не указан
        # XXX
    elif video['codec'] == 'flv':
        format_data = stdout_data['format']
        duration = format_data.get('duration')
        if duration and not video['duration']:
            result['video']['duration'] = parse_float(duration) 

    return result


def avprobe(fname):
    args = [settings.AVPROBE_BIN, '-print_format', 'json',
            '-show_format', '-show_streams', fname]
    proc = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    stdout_data = parse_stdout(stdout)
    stderr_data = parse_stderr(stderr)

    formats = stdout_data['format']['format_name'].split(',')
    extension = get_extension(fname)
    format = extension in formats and extension or formats[0]

    video = None
    audio = None
    for stream in stdout_data['streams']:
        if not video and stream['codec_type'] == 'video':
            video = extract_video_data(stream, stderr_data)
        if not audio and stream['codec_type'] == 'audio':
            audio = extract_audio_data(stream, stderr_data)

    result = {
        'video': video,
        'audio': audio,
        'format': format
    }
    result = apply_hacks(result, stdout_data, stderr_data)
    return result


"""
Некоторые кодеки имеют енкодеры, названия которых отличаются от имени кодека:
"""
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
        'mpeg2': 'mpeg2video',
        'jpeg': 'mjpeg'
    }
}


"""
Некоторые енкодеры требуют специальных аргументов:
"""
encoder_args = {
    'acodecs': {
        'aac': ['-strict', 'experimental']
    },
    'vcodecs': {
        'h263p': ['-threads', '1'],
        'libtheora': ['-qscale', '6'],
        'libx264': ['-flags', '+loop', '-cmp', '+chroma', '-partitions',
                    '+parti4x4+partp8x8+partb8x8', '-subq', '5', '-trellis', '1', '-refs', '1',
                    '-coder', '0', '-me_range', '16', '-g', '300', '-keyint_min', '25',
                    '-sc_threshold', '40', '-i_qfactor', '0.71', '-rc_eq', "'blurCplx^(1-qComp)'",
                    '-qcomp', '0.6', '-qmin', '10', '-qmax', '51', '-qdiff', '4', '-level', '30']
    }
}


"""
Некоторые форматы называются в ffmpeg иначе:
"""
format_aliases = {
    'mpeg': 'mpegts',
    'mpg': 'mpegts',
    'mkv': 'matroska',
    'm4a': 'mov'
}


"""
Таблица дефолтных форматов для аудио, закодированных соответствующим кодеком:
"""
acodec_to_format_map = {
    'vorbis': 'ogg',
    'flac': 'flac',
    'alac': 'm4a',
    'mp3': 'mp3',
    'aac': 'mp4',
    'ac3': 'ac3'
}


def avconv(source_fname, target_fname, options):
    args = [settings.AVCONV_BIN, '-i', source_fname]

    position = options.get('position')
    if position:
        args.extend(['-ss', position ])

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
    else:
        args.append('-an')

    video_options = options.get('video')
    if video_options:
        codec = video_options.get('codec')
        if codec:
            encoder_name = encoders['vcodecs'].get(codec, codec)
            args.extend(['-vcodec', encoder_name])
            args.extend(encoder_args['vcodecs'].get(encoder_name, []))
        fps = video_options.get('fps')
        if fps:
            args.extend(['-r', str(fps)])
        bitrate = video_options.get('bitrate')
        if bitrate:
            args.extend(['-b', str(bitrate)])
        filters = video_options.get('filters')
        if filters:
            args.extend(['-vf', filters])
        frames = video_options.get('frames')
        if frames:
            args.extend(['-vframes', frames])
    else:
        args.append('-vn')

    format = options['format']
    avconv_format_name = format_aliases.get(format, format)
    args.extend(['-f', avconv_format_name, '-y', target_fname])
    
    proc = subprocess.Popen(args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.communicate()
    return proc.returncode


def get_codec_supported_actions(codec_type, codec_name):
    """Возвращает информацию о том, какие действия поддерживает кодек (decoding, encoding).
    :param codec_type: 'audio' или 'video'
    :param codec_name: название кодека в терминах ffmpeg
    :rtype: `dict(decoding=bool, encoding=bool)`
    """
    key = (codec_type == 'audio' and 'acodecs') or \
          (codec_type == 'video' and 'vcodecs')

    codec = avconv_db[key].get(codec_name)

    if codec_name in encoders[key]:
        encoder_name = encoders[key][codec_name]
        encoder = avconv_db[key].get(encoder_name)
        codec['encoding'] = codec['encoding'] or (encoder and encoder['encoding'])

    return codec
