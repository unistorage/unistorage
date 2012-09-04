from PIL import Image
from utils import *
from ..utils import ValidationError


name = 'convert'
type_families_applicable_for = ['image']
result_type_family = 'image'


def validate_and_get_args(source_file, args):
    if 'to' not in args:
        raise ValidationError('`to` must be specified.')
    format = args['to']

    supported_formats = ('bmp', 'gif', 'jpeg', 'png', 'tiff')
    if format not in supported_formats:
        raise ValidationError('Source file is %s and can be only converted to the one of '
            'following formats: %s.' % (source_file.content_type, ', '.join(supported_formats)))

    return [format]


def perform(source_file, to):
    source_image = Image.open(source_file)
    target_image = wrap(source_image)
    return target_image.finalize(format=to)
