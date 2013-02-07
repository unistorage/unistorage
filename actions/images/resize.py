from actions.common import validate_presence
from actions.common.resize_validation import validate_and_get_args
from identify import identify
from . import ImageMagickWrapper


name = 'resize'
applicable_for = 'image'
result_unistorage_type = 'image'


def to_int(x):
    return int(round(x, 0))


def perform(source_file, mode, target_width, target_height):
    target_image = ImageMagickWrapper(source_file)

    if mode == 'resize':
        return target_image.resize(target_width, target_height).finalize()
    
    image_data = identify(source_file)
    source_width, source_height = image_data['width'], image_data['height']

    # If mode == 'keep', either target_width or target_height can be None
    factors = [float(target_width) / source_width if target_width else 1.0,
               float(target_height) / source_height if target_height else 1.0]

    factor = max(factors) if mode == 'crop' else min(factors)
    width = to_int(source_width * factor)
    height = to_int(source_height * factor)

    if factor < 1:
        target_image.resize(width, height)

        if mode == 'crop':
            target_image.crop_to_center(target_width, target_height)

    return target_image.finalize()
