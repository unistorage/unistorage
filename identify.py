# coding: utf-8
"""
Обертка над консольной утилитой `identify`.
"""
import json
import subprocess

import settings


class IdentifyException(Exception):
    pass


def identify(file_):
    identify_format = '{"width": %w, "height": %h, "format": "%m"}\n'
    args = [settings.IDENTIFY_BIN, '-format', identify_format, '-']
    
    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)

    buffer_ = file_.read()
    file_.seek(0)

    stdout_data, stderr_data = proc.communicate(input=buffer_)
    if proc.returncode != 0:
        raise IdentifyException('Error during `identify` call: "%s".' % stderr_data)

    try:
        frames = map(json.loads, stdout_data.strip().split('\n'))
    except:
        raise IdentifyException('Could not decode data `identify` output.')

    result = frames[0]
    result['format'] = result['format'].lower()
    result['is_animated'] = len(frames) > 1
    return result
