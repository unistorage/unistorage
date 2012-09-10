import os
import subprocess

import gridfs
from flask import g
from bson.objectid import ObjectId
from PIL import Image
from utils import *
from actions.utils import ValidationError, get_type_family


name = 'watermark'
applicable_for = 'image'
result_type_family = 'image'


def validate_presence(args, arg_name):
    if arg_name not in args:
        raise ValidationError('`%s` must be specified.' % arg_name)


def validate_and_get_as_dimension(args, arg_name):
    str_value = args[arg_name]
    is_in_pixels = str_value.endswith('px')
    
    try:
        int_value = int(str_value[0:-2] if is_in_pixels else str_value)
    except ValueError:
        raise ValidationError('`%s` must be an integer (possibly suffixed by "px").' % arg_name)

    if is_in_pixels:
        return int_value

    if 0 <= int_value <= 100:
        return int_value / 100.
    else:
        raise ValidationError('Percent value `%s` must be between 0 and 100.' % arg_name)


def validate_and_get_args(args):
    for arg_name in ('w', 'h', 'h_pad', 'v_pad', 'corner', 'watermark_id'):
        validate_presence(args, arg_name)
    
    w, h, hpad, vpad = [validate_and_get_as_dimension(args, arg_name) \
            for arg_name in ('w', 'h', 'h_pad', 'v_pad')]
        
    corners = ('ne', 'se', 'sw', 'nw')
    corner = args['corner']
    if corner not in corners:
        raise ValidationError('`corner` must be one of the following: %s.' % ', '.join(corners))

    watermark_id = args['watermark_id']
    try:
        watermark = g.fs.get(ObjectId(args['watermark_id']))
    except gridfs.errors.NoFile:
        raise ValidationError('File with id %s does not exist.' % watermark_id)
    
    if get_type_family(watermark.content_type) != 'image':
        raise ValidationError('File with id %s is not an image.' % watermark_id)

    return [watermark_id, w, h, hpad, vpad, corner]


CORNER_MAP = {
    'ne': 'NorthEast',
    'se': 'SouthEast',
    'sw': 'SouthWest',
    'nw': 'NorthWest',
}


def identify(file, format):
    args = ['identify', '-format', format, '-']
    proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = proc.communicate(input=file.read())
    file.seek(0)
    if proc.returncode != 0:
        raise Exception('`identify` failed: %s' % stderr_data)
    return stdout_data.strip()


def get_watermark_bbox_geometry(source_width, source_height, w, h, h_pad, v_pad):
    """Returns watermark bounding box geometry"""
    is_float = lambda value: isinstance(value, float)
    bbox_width = round(source_width * w) if is_float(w) else w
    bbox_height = round(source_height * h) if is_float(h) else h
    bbox_h_offset = round(source_width * h_pad) if is_float(h_pad) else h_pad
    bbox_v_offset = round(source_height * v_pad) if is_float(v_pad) else v_pad
    return '%dx%d+%d+%d' % (bbox_width, bbox_height, bbox_h_offset, bbox_v_offset)


def perform(source_file, watermark_id, w, h, h_pad, v_pad, corner):
    source_format, source_size = identify(source_file, '%m %wx%h').split()
    source_width, source_height = map(int, source_size.split('x'))

    watermark = g.fs.get(ObjectId(watermark_id))
    watermark_format = identify(watermark, '%m')
    watermark_bbox_geometry = get_watermark_bbox_geometry(
            source_width, source_height, w, h, h_pad, v_pad)

    fd_in, fd_out = os.pipe()
    args = ['composite', '-gravity', CORNER_MAP[corner],
            '-geometry', watermark_bbox_geometry,
            '%s:fd:%d' % (watermark_format, fd_in), '-', '-']
    proc = subprocess.Popen(args, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.write(fd_out, watermark.read())
    os.close(fd_out)

    stdout, stderr = proc.communicate(input=source_file.read())
    return StringIO(stdout), source_format.lower()
