import gridfs
from flask import g
from bson.objectid import ObjectId

from actions.utils import ValidationError, get_type_family


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
        watermark = g.fs.get(ObjectId(watermark_id))
    except gridfs.errors.NoFile:
        raise ValidationError('File with id %s does not exist.' % watermark_id)
    
    if get_type_family(watermark.content_type) != 'image':
        raise ValidationError('File with id %s is not an image.' % watermark_id)

    return [ObjectId(watermark_id), w, h, hpad, vpad, corner]
