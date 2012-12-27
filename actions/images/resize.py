from actions.common import validate_presence
from actions.common.resize_validation import validate_and_get_args


name = 'resize'
applicable_for = 'image'
result_unistorage_type = 'image'


def perform(source_file, mode, target_width, target_height):
    from PIL import Image
    from utils import wrap, to_int

    source_image = Image.open(source_file)
    target_image = wrap(source_image)

    if mode == 'resize':
        return target_image.resize(target_width, target_height).finalize()

    source_width, source_height = map(float, source_image.size)
    # If mode == 'keep', either target_width or target_height can be None
    factors = [target_width / source_width if target_width else 1,
               target_height / source_height if target_height else 1]

    factor = max(factors) if mode == 'crop' else min(factors)
    width = to_int(source_width * factor)
    height = to_int(source_height * factor)

    if factor < 1:
        target_image.resize(width, height)

        if mode == 'crop':
            target_image.crop_to_center(target_width, target_height)

    return target_image.finalize()
