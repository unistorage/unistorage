import gridfs
from flask import g, current_app

from app import parse_file_uri
from actions.utils import ValidationError, get_type_family
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


def validate_and_get_args(args):
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
        watermark = g.fs.get(watermark_id)
    except gridfs.errors.NoFile:
        raise ValidationError('File with id %s does not exist.' % watermark_id)
    
    if get_type_family(watermark.content_type) != 'image':
        raise ValidationError('File with id %s is not an image.' % watermark_id)

    return [watermark_id, w, h, w_pad, h_pad, corner]
