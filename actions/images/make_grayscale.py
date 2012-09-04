from PIL import Image
from utils import *
from ..utils import ValidationError


name = 'make_grayscale'
type_families_applicable_for = ['image']
result_type_family = 'image'


def validate_and_get_args(source_file, args):
    return []


def perform(source_file):
    source_image = Image.open(source_file)
    target_image = wrap(source_image)
    return target_image.make_grayscale().finalize()
