# coding: utf-8
"""
Обертка над консольной утилитой `identify`.
"""
import json
import subprocess

import settings


class IdentifyException(Exception):
    pass


def identify_buffer(buffer_):
    """Возвращает информацию об изображении, содержащемся в
    наборе байтов `buffer_`. Возвращает то же самое, что и
    :func:`identify_file`.
    """
    identify_format = '{"width": %w, "height": %h, "format": "%m", ' \
                      '"orientation": "%[EXIF:Orientation]"}\n'
    args = [settings.IDENTIFY_BIN, '-format', identify_format, '-']
    
    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    stdout_data, stderr_data = proc.communicate(input=buffer_)
    if proc.returncode != 0:
        raise IdentifyException('Error during `identify` call: "%s".' % stderr_data)

    try:
        frames = map(json.loads, stdout_data.strip().split('\n'))
    except:
        raise IdentifyException('Can\'t decode data `identify` output.')

    result = frames[0]
    result['format'] = result['format'].lower()
    result['is_animated'] = len(frames) > 1
    try:
        result['orientation'] = int(result['orientation'])
    except ValueError:
        result['orientation'] = 1
    return result


def identify_file(file_):
    """Возвращает информацию об изображении, содержащемся в
    file-like object `file_`.

    :rtype: словарь вида ``
        {
            width: int,
            height: int,
            format: basestring,
            orientation: int,  # ориентация в терминах EXIF, число от 1 до 8
            is_animated: bool,
        }
        ``
    """
    buffer_ = file_.read()
    file_.seek(0)

    return identify_buffer(buffer_)
