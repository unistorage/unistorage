# coding: utf-8
from actions.utils import ValidationError
from actions.common import validate_presence
from . import ImageMagickWrapper


name = 'rotate'
applicable_for = 'image'


def get_result_unistorage_type(*args):
    return 'image'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'angle')
    angle = args['angle']

    if angle not in ('90', '180', '270'):
        raise ValidationError('Unsupported `angle` value. Available values: 90, 180, 270.')

    return [int(angle)]


def perform(source_file, angle):
    # Удаляем EXIF-информацию, чтобы затереть тег Orientation
    return ImageMagickWrapper(source_file).rotate(angle).strip_exif().finalize()
