from PIL import Image

from utils import *
from ..utils import ValidationError


name = 'grayscale'
applicable_for = 'image'
result_type_family = 'image'


def validate_and_get_args(args):
    return []


def perform(source_file):
    source_image = Image.open(source_file)
    target_image = wrap(source_image)
    return target_image.make_grayscale().finalize()
