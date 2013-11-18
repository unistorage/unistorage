# coding: utf-8
import re
import json
import pipes
import os.path
import logging
import tempfile
import subprocess
import cPickle as pickle
from StringIO import StringIO
from datetime import datetime, timedelta

import newrelic.agent
import magic

import settings


logger = logging.getLogger(__name__)


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


def get_first_sane_duration(durations):
    for duration in durations:
        if duration and duration < 24 * 60 * 60:
            return duration
    return None


def extract_video_data(stream, stderr_data):
    """Парсит сырые данные, полученные от ffmpeg. Возвращает только нужные поля,
    приведённые к своим типам -- словарь, удовлетворяющий следующей схеме:
    ```
    {
        'width': int,
        'height': int,
        'codec': string,  # имя кодека в терминологии ffmpeg
        'bitrate': int,  # битрейт
        'duration': float,  # длительность видео в секундах
        'fps': float,  # frame per second
    }
    ```

    :param stream: словарь, содержащий данные о потоке из stdout-а ffmpeg
    :param stderr_data: словарь, содержащие данные из stderr-а ffmpeg
    """
    def parse_avg_frame_rate(val):
        """Парсит FPS в ffmpeg-овском формате, возвращает `float`."""
        if '/' in val:
            n, d = map(parse_float, val.split('/'))
            return n and d and n / d
        elif '.' in val:
            return parse_float(val)

    duration = parse_float(stream.get('duration')) or \
        parse_float(stderr_data.get('duration'))

    video_bitrate = stderr_data.get('video_bitrate')
    if not video_bitrate:
        file_bitrate = stderr_data.get('file_bitrate')
        audio_bitrate = stderr_data.get('audio_bitrate')
        if file_bitrate and audio_bitrate:
            video_bitrate = file_bitrate - audio_bitrate
    return {
        'width': parse_int(stream.get('width')),
        'height': parse_int(stream.get('height')),
        'codec': stream.get('codec_name'),
        'bitrate': video_bitrate,
        'duration': duration,
        'fps': parse_avg_frame_rate(stream.get('avg_frame_rate')) or
               parse_avg_frame_rate(stream.get('r_frame_rate')),
    }


def extract_audio_data(stream, stderr_data):
    """Парсит сырые данные, полученные от ffmpeg. Возвращает только нужные поля,
    приведённые к своим типам -- словарь, удовлетворяющий следующей схеме:
    ```
    {
        'channels': int,  # количество каналов
        'sample_rate': float,
        'codec': string,  # имя кодека в терминологии ffmpeg
        'bitrate': int,
        'duration': float,  # длительность видео в секундах
    }
    ```

    :param stream: словарь, содержащий данные о потоке из stdout-а ffmpeg
    :param stderr_data: словарь, содержащие данные из stderr-а ffmpeg
    """
    duration = parse_float(stream.get('duration')) or \
        parse_float(stderr_data.get('duration'))
    return {
        'channels': parse_int(stream.get('channels')),
        'sample_rate': parse_float(stream.get('sample_rate')),
        'codec': stream.get('codec_name'),
        'bitrate': stderr_data.get('audio_bitrate'),
        'duration': duration
    }


def parse_stdout(stdout):
    return json.loads(unicode(stdout, errors='replace'))


def parse_stderr(stderr):
    """Парсит stderr ffmpeg-а и извлекает из него битрейты первых встреченных
    аудио- и видеопотоков (ffmpeg выдаёт эти данные _только_ в stderr).
    Возвращает словарь, удовлетворяющий следующей схеме:
    ```
    {
        'audio_bitrate': int or None,
        'video_bitrate': int or None,
        'file_bitrate': int or None,  # Общий битрейт файла
        'video_size': str or None,  # Размер видео в формате \d+x\d+
        'duration': float or None,  # Общая продолжительность файла
    }
    """
    data = {
        'audio_bitrate': None,
        'video_bitrate': None,
        'file_bitrate': None,
        'video_size': None,
        'duration': None,
    }
    regexp = r'Stream.*(?P<stream_type>Audio|Video):.*?(?P<bitrate>\d+) kb/s'
    for match in re.finditer(regexp, stderr):
        stream_type = match.group('stream_type').lower()
        key = '%s_bitrate' % stream_type
        if not data[key]:
            data[key] = int(match.group('bitrate')) * 1000

    regexp = '\n\s+Duration:.*?, bitrate: (?P<bitrate>\d+) kb/s\n'
    match = re.search(regexp, stderr)
    if match:
        data['file_bitrate'] = int(match.group('bitrate')) * 1000

    regexp = r'Stream.*Video:.*?\s(?P<size>\d+x\d+)(?:,|\n)'
    match = re.search(regexp, stderr)
    if match:
        data['video_size'] = match.group('size')

    regexp = r'Duration: (?P<duration>\d+:\d+:\d+\.\d+)'
    match = re.search(regexp, stderr)
    if match:
        try:
            d = datetime.strptime(match.group('duration'), '%H:%M:%S.%f')
            duration = timedelta(
                hours=d.hour, minutes=d.minute,
                seconds=d.second, microseconds=d.microsecond)
            data['duration'] = duration.total_seconds()
        except:
            pass
    return data


def get_extension(fname):
    extension = None
    if '.' in fname:
        _, extension = os.path.splitext(fname)
    return extension and extension.lstrip('.')


def apply_hacks(result, stdout_data, stderr_data, fname):
    video = result['video']
    audio = result['audio']

    if not video:
        return result

    if video['codec'] == 'vp6f':
        # 1. Битрейт и длительность находятся в секции format
        format_data = stdout_data['format']
        bitrate = format_data.get('bit_rate')
        if bitrate and not video['bitrate']:
            result['video']['bitrate'] = int(parse_float(bitrate) * 1000)

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
        if audio and not audio['duration']:
            audio['duration'] = result['video']['duration']

        # 4. FPS и вовсе нигде не указан
        # XXX
    elif video['codec'] == 'flv':
        format_data = stdout_data['format']
        duration = format_data.get('duration')
        if duration and not video['duration']:
            result['video']['duration'] = parse_float(duration)

    if video and video['fps'] == 1000:
        video['fps'] = 25

    # Решаем проблему с неправдоподобными длительностями:
    format_duration = stderr_data.get('duration')
    video_duration = video and video['duration']
    audio_duration = audio and audio['duration']
    if video:
        result['video']['duration'] = get_first_sane_duration(
            [video_duration, format_duration, audio_duration])
    if audio:
        result['audio']['duration'] = get_first_sane_duration(
            [audio_duration, format_duration, video_duration])

    if video and (not audio) and (not video['bitrate']):
        result['video']['bitrate'] = stderr_data.get('file_bitrate')

    # Если webm закачивается без расширения, ffmpeg выдаёт формат matroska
    if result['format'] == 'matroska':
        from file_utils import get_content_type_from_buffer
        with open(fname) as file:
            content_type = get_content_type_from_buffer(file.read(1024))

        if content_type == 'video/webm':
            result['format'] = 'webm'

    # Для видео, у которых известен только битрейт всего файла
    if stderr_data.get('file_bitrate') and \
            (audio and not audio['bitrate']) and (video and not video['bitrate']):

        cmd = '%s -i %s -vn -acodec copy -f %s -y - | wc -c' % \
            (settings.AVCONV_BIN, pipes.quote(fname), pipes.quote(result['format']))
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()
        try:
            audio_size = int(stdout)  # размер аудиопотока в байтах
            result['audio']['bitrate'] = int(audio_size * 8. / audio_duration)
        except:
            pass

    # Решаем проблему, когда известен только один из битрейтов -- аудио или видео
    file_bitrate = stderr_data.get('file_bitrate')
    file_duration = get_first_sane_duration(
        [format_duration, video_duration, audio_duration])
    file_size = stdout_data.get('format', {}).get('size')
    if not file_bitrate and file_duration and file_size:
        try:
            file_bitrate = int(float(file_size) * 8 / file_duration)
        except:
            pass

    if file_bitrate and video and audio:
        video_bitrate = video['bitrate']
        audio_bitrate = audio['bitrate']
        if (not video_bitrate) and audio_bitrate:
            video['bitrate'] = file_bitrate - audio_bitrate
        if (not audio_bitrate) and video_bitrate:
            audio['bitrate'] = file_bitrate - video_bitrate

    return result


def get_sanest_stream(streams, stderr_data, parser):
    """Возвращает распарсенным тот единственный поток,
    который будет отображаться в метаданных файла.
    """
    prioritized_streams = []
    for stream in streams:
        priority = 0
        parsed_stream = parser(stream, stderr_data)
        if stream.get('profile') == 'Main':
            priority += 5
        if 0 < parsed_stream.get('fps', 0) < 100:  # Если разумный битрейт
            priority += 3
        prioritized_streams.append((priority, parsed_stream))
    prioritized_streams.sort()
    _, parsed_stream = prioritized_streams and prioritized_streams[-1] or (None, None)
    return parsed_stream


@newrelic.agent.function_trace()
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
    video_streams = []
    audio_streams = []
    for stream in stdout_data['streams']:
        if stream.get('codec_name', 'unknown') == 'unknown':
            continue
        if stream.get('codec_type') == 'video':
            video_streams.append(stream)
        if stream.get('codec_type') == 'audio':
            audio_streams.append(stream)
    result = {
        'video': get_sanest_stream(video_streams, stderr_data, extract_video_data),
        'audio': get_sanest_stream(audio_streams, stderr_data, extract_audio_data),
        'format': format,
    }
    return apply_hacks(result, stdout_data, stderr_data, fname)


def avprobe_buffer(data):
    with tempfile.NamedTemporaryFile(mode='wb') as tmp_file:
        tmp_file.write(data)
        tmp_file.flush()
        return avprobe(tmp_file.name)


"""
Некоторые кодеки имеют енкодеры, названия которых отличаются от имени кодека:
"""
encoders = {
    'acodecs': {
        'vorbis': 'libvorbis',
        'mp3': 'libmp3lame',
    },
    'vcodecs': {
        'theora': 'libtheora',
        'h264': 'libx264',
        'divx': 'mpeg4',
        'vp8': 'libvpx',
        'h263': 'h263p',
        'mpeg1': 'mpeg1video',
        'mpeg2': 'mpeg2video',
        'jpeg': 'mjpeg',
    },
}


"""
Некоторые енкодеры требуют специальных аргументов:
"""
encoder_args = {
    'acodecs': {
        'aac': ['-strict', 'experimental'],
    },
    'vcodecs': {
        'h263p': ['-threads', '1', '-vf', 'scale=trunc(iw/4)*4:trunc(ih/4)*4'],
        'libtheora': ['-qscale', '6'],
        'libx264': ['-vprofile', 'main', '-flags', '+loop', '-cmp', 'chroma', '-partitions',
                    'parti4x4+partp8x8+partb8x8', '-subq', '5', '-trellis', '1', '-refs', '1',
                    '-coder', '0', '-me_range', '16', '-g', '300', '-keyint_min', '25',
                    '-sc_threshold', '40', '-i_qfactor', '0.71', '-rc_eq', "'blurCplx^(1-qComp)'",
                    '-qcomp', '0.6', '-qmin', '10', '-qmax', '51', '-qdiff', '4', '-level', '30',
                    '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2'],  # h264 поддерживает только четные длину и высоту
    },
}


"""
Некоторые форматы требуют специальных аргументов:
"""
format_args = {
    'mov': ['-movflags', 'faststart'],
    'mp4': ['-movflags', 'faststart'],
}


"""
Некоторые форматы называются в ffmpeg иначе:
"""
format_aliases = {
    'mpeg': 'mpegts',
    'mpg': 'mpegts',
    'mkv': 'matroska',
    'm4a': 'mov',
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
    'ac3': 'ac3',
}


def avconv(source_fname, target_fname, options):
    args = [settings.AVCONV_BIN, '-i', source_fname]

    position = options.get('position')
    if position:
        args.extend(['-ss', position])

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
            if fps < 1:  # Хотим конвертить странные битые видео
                fps = 1
            args.extend(['-r', '%.4f' % fps])
        bitrate = video_options.get('bitrate')
        if bitrate:
            args.extend(['-v:b', str(bitrate)])
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
    args.extend(format_args.get(avconv_format_name, []))
    args.extend(['-f', avconv_format_name, '-y', target_fname])
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()

    return_code = proc.wait()
    if return_code not in (0, 254):
        raise Exception(stdout + stderr)

    if return_code == 254:
        logger.warning('Probably incorrect source file?',
                       extra={'ffmpeg_command': ' '.join(args)})

    if format == 'flv':
        proc = subprocess.Popen([settings.FLVTOOL_BIN, '-U', target_fname],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.wait() != 0:
            raise Exception(stdout + stderr)

    return target_fname


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
