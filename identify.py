# coding: utf-8
"""
Обертка над консольной утилитой `identify`.
"""
import json
import subprocess

import settings


class IdentifyException(Exception):
    pass


def _run_identify(format, buffer):
    args = [settings.IDENTIFY_BIN, '-format', format, '-']

    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    stdout_data, stderr_data = proc.communicate(input=buffer)
    if proc.returncode != 0:
        raise IdentifyException('Error during `identify` call: "%s".' % stderr_data)

    try:
        rows = map(json.loads, stdout_data.strip().split('\n'))
    except:
        raise IdentifyException('Can\'t decode data `identify` output.')
    return rows


def identify_buffer(buffer):
    """Возвращает информацию об изображении, содержащемся в
    наборе байтов `buffer_`. Возвращает то же самое, что и
    :func:`identify_file`.
    """
    frames = _run_identify('{"width": %w, "height": %h, "format": "%m"}\n', buffer)

    result = frames[0]
    result['format'] = result['format'].lower()
    result['is_animated'] = len(frames) > 1
    try:
        # %[EXIF:Orientation] роняет identify в некоторых случаях (баг ImageMagick),
        # поэтому молча проглатываем все исключения
        orientations = _run_identify('{"orientation": "%[EXIF:Orientation]"}\n', buffer)
        result['orientation'] = int(orientations[0]['orientation'])
    except:
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
