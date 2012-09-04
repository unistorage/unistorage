import subprocess
from StringIO import StringIO

from PIL import Image, ImageOps

import settings
from tasks import ActionException


def to_int(x):
    return int(round(x, 0))


def is_animated(image):
    try:
        image.seek(1)
    except EOFError:
        is_animated = False
    else:
        is_animated = True
    image.seek(0)
    return is_animated


def is_rgba_png(image):
    return image.mode == 'RGBA'


class PILWrapper(object):
    def __init__(self, image):
        self._image = image
        self._format = self._image.format.upper()
    
    def make_grayscale(self):
        self._image = ImageOps.grayscale(self._image)
        return self

    def resize(self, width, height):
        self._image = self._image.resize((width, height), resample=Image.ANTIALIAS)
        return self
    
    def crop_to_center(self, target_width, target_height):
        width, height = self._image.size
        width_to_crop = width - target_width
        height_to_crop = height - target_height

        left, top = to_int(width_to_crop / 2), to_int(height_to_crop / 2)
        right, bottom = width - left, height - top

        self._image = self._image.crop((left, top, right, bottom))
        return self

    def finalize(self, **kwargs):
        format = kwargs.get('format', self._format).upper()
        if self._image.mode != 'RGB' and format in ('JPEG', 'BMP'):
            self._image = self._image.convert('RGB')
        result = StringIO()
        self._image.save(result, format)
        return result, format.lower()


class ImageMagickWrapper(object):
    def __init__(self, image):
        self._image = image
        self._is_animated = is_animated(self._image)
        self._format = self._image.format.upper()
        self._args = [settings.CONVERT_BIN, '-']
    
    def make_grayscale(self):
        self._args.extend(['-colorspace', 'gray'])
        return self

    def resize(self, width, height):
        self._args.extend(['-resize', '%dx%d!' % (width, height)])
        return self
    
    def crop_to_center(self, width, height):
        self._args.extend(['-gravity', 'Center',
                '-crop', '%dx%d+0+0' % (width, height), '+repage'])
        return self

    def finalize(self, **kwargs):
        format = kwargs.get('format', self._format).upper()

        if self._is_animated and format != self._format:
            # If converting from animated image to static, specify frame number
            self._args[1] += '[0]'
        else:
            self._args.insert(2, '-coalesce')

        self._args.append('%s:-' % format.upper())
        proc_input = self._image.fp
        proc_input.seek(0)

        try:
            proc = subprocess.Popen(self._args, stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise ActionException('Failed to start ImageMagick\'s convert: %s' % self._args[0])

        result, error = proc.communicate(input=proc_input.read())
        return_code = proc.wait()
        if return_code != 0:
            raise ActionException('ImageMagick\'s convert (%s) failed.' % self._args[0])

        return StringIO(result), format.lower()


def wrap(image):
    if image.format == 'GIF' or is_rgba_png(image):
        wrapper = ImageMagickWrapper
    else:
        wrapper = PILWrapper 
    return wrapper(image)
