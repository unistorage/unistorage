from actions.utils import ValidationError
from actions.common import validate_presence
from . import ImageMagickWrapper


name = 'crop'
applicable_for = 'image'


def get_result_unistorage_type(*args):
    return 'image'


def validate_and_get_args(args, source_file=None):
    arg_names = ('x1', 'y1', 'x2', 'y2')
    for arg_name in arg_names:
        validate_presence(args, arg_name)

    try:
        x1, y1, x2, y2 = map(int, map(args.get, arg_names))
    except ValueError:
        raise ValidationError('`x1`, `y1`, `x2`, `y2` must be integer values.')

    if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
        raise ValidationError('`x1`, `y1`, `x2`, `y2` must be positive integer values.')

    if x2 <= x1:
        raise ValidationError('`x1` must be strictly less than `x2`.')
    if y2 <= y1:
        raise ValidationError('`y1` must be strictly less than `y2`.')

    if source_file:
        assert source_file.unistorage_type == 'image'
        width = source_file.extra['width']
        height = source_file.extra['height']
        if x2 > width or y2 > height:
            raise ValidationError('`(x2, y2)` is out of the image boundaries.')

    return [x1, y1, x2, y2]


def perform(source_file, x1, y1, x2, y2):
    print x1, y1, x2, y2
    return ImageMagickWrapper(source_file).crop(x1, y1, x2, y2).finalize()
