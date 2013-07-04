import os
import subprocess
from cStringIO import StringIO

import settings
import actions
from actions.common.watermark_validation import \
    get_watermark_bbox_geometry, \
    validate_and_get_args as common_validate_and_get_args
from identify import identify_file
from actions.images.resize import perform as image_resize
from actions.utils import ActionError


name = 'watermark'
applicable_for = 'image'
validate_and_get_args = common_validate_and_get_args


def get_result_unistorage_type(*args):
    return 'image'


CORNER_MAP = {
    'ne': 'NorthEast',
    'se': 'SouthEast',
    'sw': 'SouthWest',
    'nw': 'NorthWest',
}


def resize_watermark(wm, wm_bbox):
    resized_wm, resized_wm_ext = image_resize(wm, 'keep', *wm_bbox)
    return resized_wm


def perform(source_file, watermark_file, w, h, h_pad, v_pad, corner):
    source_data = identify_file(source_file)
    watermark_format = identify_file(watermark_file)['format']
    watermark_bbox_geometry = get_watermark_bbox_geometry(
        source_data['width'], source_data['height'], w, h, h_pad, v_pad)
    watermark_bbox_geometry_str = '%dx%d+%d+%d' % watermark_bbox_geometry

    fd = os.tmpfile()
    args = [
        settings.CONVERT_BIN, '-', '-coalesce', '-gravity', CORNER_MAP[corner],
        '-geometry', watermark_bbox_geometry_str, 'null:',
        '%s:fd:%d' % (watermark_format, fd.fileno()), '-layers', 'composite', '-',
    ]
    resized_wm = resize_watermark(watermark_file, watermark_bbox_geometry[:2])
    fd.write(resized_wm.read())
    fd.seek(0)
    proc = subprocess.Popen(
        args, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate(input=source_file.read())
    fd.close()

    if proc.returncode != 0:
        raise ActionError('`composite` failed: %s' % stderr_data)
    return StringIO(stdout_data), source_data['format']
