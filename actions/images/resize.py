from actions.common.resize_validation import validate_and_get_args \
    as common_resize_validate_and_get_args
from identify import identify_file
from . import ImageMagickWrapper
from actions.utils import ValidationError


name = 'resize'
applicable_for = 'image'


def get_result_unistorage_type(*args):
    return 'image'


def to_int(x):
    return int(round(x, 0))


def validate_and_get_args(args, source_file=None):
    mode, w, h = common_resize_validate_and_get_args(args, source_file)
    if source_file:
        width = source_file.extra['width']
        height = source_file.extra['height']
        if width > w or height > h:
            raise ValidationError('Upscale is forbidden.')

    return [mode, w, h]


def perform(source_file, mode, target_width, target_height):
    target_image = ImageMagickWrapper(source_file)

    if mode == 'resize':
        return target_image.resize(
            to_int(target_width), to_int(target_height)).finalize()

    image_data = identify_file(source_file)
    source_width, source_height = image_data['width'], image_data['height']

    # If mode == 'keep', either target_width or target_height can be None
    factors = []
    if target_width is not None:
        factors.append(float(target_width) / source_width)
    if target_height is not None:
        factors.append(float(target_height) / source_height)
    assert target_width or target_height

    factor = max(factors) if mode == 'crop' else min(factors)
    width = to_int(source_width * factor)
    height = to_int(source_height * factor)

    target_image.resize(width, height)
    if mode == 'crop':
        target_image.crop_to_center(target_width, target_height)

    return target_image.finalize()
