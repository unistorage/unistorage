import subprocess
from StringIO import StringIO

from PIL import Image

import settings


def to_int(x):
    return int(round(x, 0))

def is_animated(image):
    try:
        image.seek(1)
    except EOFError:
        return False
    else:
        return True

class PILWrapper(object):
    def __init__(self, image):
        self._image = image
        self._format = self._image.format
    
    def resize(self, width, height):
        self._image = self._image.resize((width, height), resample=Image.ANTIALIAS)
        return self
    
    def crop_to_center(self, target_width, target_height):
        width, height = map(float, self._image.size)
        width_to_crop = width - target_width
        height_to_crop = height - target_height

        left, top = to_int(width_to_crop / 2), to_int(height_to_crop / 2)
        right, bottom = width - left, height - top

        self._image = self._image.crop((left, top, right, bottom))
        return self

    def finalize(self):
        data = StringIO()
        self._image.save(data, self._format)
        return data

class ImageMagickWrapper(object):
    def __init__(self, image):
        self._image = image
        self._format = self._image.format
        self._args = [settings.CONVERT_BIN, '-', '-coalesce']
    
    def resize(self, width, height):
        self._args.extend(['-resize', '%dx%d!' % (width, height)])
        return self
    
    def crop_to_center(self, width, height):
        self._args.extend(['-gravity', 'Center',
                '-crop', '%dx%d+0+0' % (width, height), '+repage'])
        return self

    def finalize(self):
        self._args.append('%s:-' % self._format)
        proc = subprocess.Popen(self._args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        proc_input = self._image.fp
        proc_input.seek(0)
        stdout_data, stderr_data = proc.communicate(input=proc_input.read())
        return StringIO(stdout_data)

def resize(source_file, mode, target_width, target_height):
    """
    Takes file-like object `source_file` and returns StringIO
    containing resulting image.
    """
    source_image = Image.open(source_file)
    
    if is_animated(source_image):
        wrap = ImageMagickWrapper
    else:
        wrap = PILWrapper 
    target_image = wrap(source_image)

    if mode == 'resize':
        return target_image.resize(target_width, target_height).finalize()

    source_width, source_height = map(float, source_image.size)
    # If mode == 'keep', either target_width or target_height can be None
    factors = target_width / source_width if target_width else 1, \
              target_height / source_height if target_height else 1

    factor = max(factors) if mode == 'crop' else min(factors)
    width = to_int(source_width * factor)
    height = to_int(source_height * factor)

    target_image.resize(width, height)

    if mode == 'crop':
        target_image.crop_to_center(target_width, target_height)

    return target_image.finalize()
