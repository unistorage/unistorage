from actions.utils import ValidationError
from actions.common import validate_presence


name = 'rotate'
applicable_for = 'image'
result_type_family = 'image'


def validate_and_get_args(args, source_file=None):
    validate_presence(args, 'angle')
    angle = args['angle']

    if angle not in ('90', '180', '270'):
        raise ValidationError('Unsupported `angle` value. Available values: 90, 180, 270.')

    return [int(angle)]


def perform(source_file, angle):
    from PIL import Image
    from utils import wrap

    source_image = Image.open(source_file)
    return wrap(source_image).rotate(angle).finalize()
