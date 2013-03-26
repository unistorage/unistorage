import os
import subprocess
from cStringIO import StringIO

import settings
import actions
from actions.common.watermark_validation import \
    get_watermark_bbox_geometry, \
    validate_and_get_args as common_validate_and_get_args
from identify import identify_file
from actions import ActionException


name = 'watermark'
applicable_for = 'image'
result_unistorage_type = 'image'
validate_and_get_args = common_validate_and_get_args


CORNER_MAP = {
    'ne': 'NorthEast',
    'se': 'SouthEast',
    'sw': 'SouthWest',
    'nw': 'NorthWest',
}


def perform(source_file, watermark_file, w, h, h_pad, v_pad, corner):
    source_data = identify_file(source_file)
    watermark_format = identify_file(watermark_file)['format']

    watermark_bbox_geometry = '%dx%d+%d+%d' % get_watermark_bbox_geometry(
        source_data['width'], source_data['height'], w, h, h_pad, v_pad)

    fd_in, fd_out = os.pipe()
    args = [
        settings.CONVERT_BIN, '-', '-coalesce', '-gravity', CORNER_MAP[corner],
        '-geometry', watermark_bbox_geometry, 'null:',
        '%s:fd:%d' % (watermark_format, fd_in), '-layers', 'composite', '-'
    ]
    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.write(fd_out, watermark_file.read())
    os.close(fd_out)

    stdout_data, stderr_data = proc.communicate(input=source_file.read())
    if proc.returncode != 0:
        raise ActionException('`composite` failed: %s' % stderr_data)
    return StringIO(stdout_data), source_data['format']
