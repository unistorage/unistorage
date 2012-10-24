import os
import subprocess
from cStringIO import StringIO

import actions
import actions.common.watermark_validation
import settings
from actions import ActionException


name = 'watermark'
applicable_for = 'image'
result_type_family = 'image'
validate_and_get_args = actions.common.watermark_validation.validate_and_get_args


CORNER_MAP = {
    'ne': 'NorthEast',
    'se': 'SouthEast',
    'sw': 'SouthWest',
    'nw': 'NorthWest',
}


def identify(file, format):
    args = [settings.IDENTIFY_BIN, '-format', '%s\n' % format, '-']
    try:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise ActionException('Failed to start `identify` (%s)' % settings.IDENTIFY_BIN)
    
    proc_input = file.read()
    file.seek(0)

    stdout_data, stderr_data = proc.communicate(input=proc_input)
    if proc.returncode != 0:
        raise ActionException('`identify` failed: %s' % stderr_data)
    return stdout_data.split('\n')[0].strip()


def get_watermark_bbox_geometry(source_width, source_height, w, h, h_pad, v_pad):
    """Returns watermark bounding box geometry"""
    is_float = lambda value: isinstance(value, float)
    bbox_width = round(source_width * w) if is_float(w) else w
    bbox_height = round(source_height * h) if is_float(h) else h
    bbox_h_offset = round(source_width * h_pad) if is_float(h_pad) else h_pad
    bbox_v_offset = round(source_height * v_pad) if is_float(v_pad) else v_pad
    return '%dx%d+%d+%d' % (bbox_width, bbox_height, bbox_h_offset, bbox_v_offset)


def perform(source_file, watermark_file, w, h, h_pad, v_pad, corner):
    source_format, source_size = identify(source_file, '%m %wx%h').split()
    source_width, source_height = map(int, source_size.split('x'))

    watermark_format = identify(watermark_file, '%m')
    watermark_bbox_geometry = get_watermark_bbox_geometry(
        source_width, source_height, w, h, h_pad, v_pad)

    fd_in, fd_out = os.pipe()
    args = [settings.COMPOSITE_BIN, '-gravity', CORNER_MAP[corner],
            '-geometry', watermark_bbox_geometry,
            '%s:fd:%d' % (watermark_format, fd_in), '-', '-']

    try:
        proc = subprocess.Popen(args, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        raise ActionException('Failed to start `composite` (%s)' % settings.COMPOSITE_BIN)
    os.write(fd_out, watermark_file.read())
    os.close(fd_out)

    stdout_data, stderr_data = proc.communicate(input=source_file.read())
    if proc.returncode != 0:
        raise ActionException('`composite` failed: %s' % stderr_data)
    return StringIO(stdout_data), source_format.lower()
