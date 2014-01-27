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


def _convert_to_degress(raw_value):
    value = [part.split('/') for part in raw_value.split(',')]

    d0 = value[0][0]
    d1 = value[0][1]
    d = float(d0) / float(d1)

    m0 = value[1][0]
    m1 = value[1][1]
    m = float(m0) / float(m1)

    s0 = value[2][0]
    s1 = value[2][1]
    s = float(s0) / float(s1)

    return d + (m / 60.0) + (s / 3600.0)


def get_lat_lon(latitude, latitude_ref,
                longitude, longitude_ref):
    if latitude is not None and latitude_ref is not None:
        lat = _convert_to_degress(latitude)
        if latitude_ref != 'N':
            lat = -lat
    else:
        lat = None

    if longitude is not None and longitude_ref is not None:
        lon = _convert_to_degress(longitude)
        if longitude_ref != 'E':
            lon = -lon
    else:
        lon = None

    return lat, lon


def identify_buffer(buffer):
    """Возвращает информацию об изображении, содержащемся в
    наборе байтов `buffer_`. Возвращает то же самое, что и
    :func:`identify_file`.
    """
    frames = _run_identify('{"width": %w, "height": %h, "format": "%m"}\n', buffer)

    result = frames[0]
    result['format'] = result['format'].lower()
    result['is_animated'] = len(frames) > 1
    result['location'] = None
    result['orientation'] = 1
    try:
        data = _run_identify(
            '{'
            ' "orientation": "%[EXIF:Orientation]",'
            ' "latitude": "%[EXIF:GPSLatitude]",'
            ' "latitude_ref": "%[EXIF:GPSLatitudeRef]",'
            ' "longitude": "%[EXIF:GPSLongitude]",'
            ' "longitude_ref": "%[EXIF:GPSLongitudeRef]"'
            '}\n', buffer)[0]
        result['orientation'] = int(data['orientation'])

        lat, lon = get_lat_lon(latitude=data['latitude'],
                               latitude_ref=data['latitude_ref'],
                               longitude=data['longitude'],
                               longitude_ref=data['longitude_ref'])
        result['location'] = {
            'latitude': int(lat * 100) / 100.,
            'longitude': int(lon * 100) / 100.,
        }
    except:
        # %[EXIF:*] роняет identify в некоторых случаях (баг ImageMagick),
        # поэтому молча проглатываем все исключения
        pass
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
