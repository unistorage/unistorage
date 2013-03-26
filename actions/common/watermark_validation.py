# -*- coding: utf-8 -*-
import gridfs

from app import db, fs
from app.uris import parse_file_uri
from actions.utils import ValidationError
from actions.common import validate_presence


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


def validate_and_get_args(args, source_file=None):
    from app.models import RegularFile  # TODO Разрешить circular import как-нибудь иначе
    for arg_name in ('w', 'h', 'w_pad', 'h_pad', 'corner', 'watermark'):
        validate_presence(args, arg_name)
    
    w, h, w_pad, h_pad = [validate_and_get_as_dimension(args, arg_name)
                          for arg_name in ('w', 'h', 'w_pad', 'h_pad')]
        
    corners = ('ne', 'se', 'sw', 'nw')
    corner = args['corner']
    if corner not in corners:
        raise ValidationError('`corner` must be one of the following: %s.' % ', '.join(corners))

    watermark_uri = args['watermark']
    try:
        watermark_id = parse_file_uri(watermark_uri)
    except ValueError as e:
        raise ValidationError(e.message)

    try:
        watermark = RegularFile.get_from_fs(db, fs, _id=watermark_id)
    except gridfs.errors.NoFile:
        raise ValidationError('File with id %s does not exist.' % watermark_id)
    
    if watermark.unistorage_type != 'image':
        raise ValidationError('File with id %s is not an image.' % watermark_id)

    if source_file:
        extra = source_file.extra
        unistorage_type = source_file.unistorage_type
        if unistorage_type == 'image':
            width = extra['width']
            height = extra['height']
        elif unistorage_type == 'video':
            width = extra['video']['width']
            height = extra['video']['height']

        validate_bbox(width, height, w, h, w_pad, h_pad)

    return [watermark_id, w, h, w_pad, h_pad, corner]


def validate_bbox(source_width, source_height, w, h, w_pad, h_pad):
    wm_width, wm_height, wm_w_offset, wm_h_offset = \
        get_watermark_bbox_geometry(source_width, source_height, w, h, w_pad, h_pad)

    x1 = wm_w_offset
    y1 = wm_h_offset
    x2 = x1 + wm_width
    y2 = y1 + wm_height
    if not (0 <= x1 <= source_width and 0 <= x2 <= source_height) or \
       not (0 <= y1 <= source_width and 0 <= y2 <= source_height):
        raise ValidationError('Watermark overflows the source image!')


def get_watermark_bbox_geometry(source_width, source_height, w, h, h_pad, v_pad):
    is_float = lambda value: isinstance(value, float)
    bbox_width = round(source_width * w) if is_float(w) else w
    bbox_height = round(source_height * h) if is_float(h) else h
    bbox_h_offset = round(source_width * h_pad) if is_float(h_pad) else h_pad
    bbox_v_offset = round(source_height * v_pad) if is_float(v_pad) else v_pad
    return (bbox_width, bbox_height, bbox_h_offset, bbox_v_offset)
