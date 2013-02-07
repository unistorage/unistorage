# coding: utf-8
import subprocess
from cStringIO import StringIO

import settings
from identify import identify
from actions import ActionException


class ImageMagickWrapper(object):
    def __init__(self, image):
        self._image = image
        image_data = identify(image)
        self._is_animated = image_data['is_animated']
        self._format = image_data['format'].upper()
        self._args = [settings.CONVERT_BIN, '-']
    
    def make_grayscale(self):
        self._args.extend(['-colorspace', 'gray'])
        return self

    def resize(self, width, height):
        self._args.extend(['-resize', '%dx%d!' % (width, height)])
        return self

    def rotate(self, angle):
        # 360 - angle, т.к. imagemagick поворачивает по часовой
        self._args.extend(['-rotate', str(-angle)])
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
        proc_input = self._image #.fp
        proc_input.seek(0)

        try:
            proc = subprocess.Popen(self._args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise ActionException('Failed to start ImageMagick\'s convert: %s' % self._args[0])

        result, error = proc.communicate(input=proc_input.read())
        return_code = proc.wait()
        if return_code != 0:
            raise ActionException('ImageMagick\'s convert (%s) failed.' % self._args[0])

        return StringIO(result), format.lower()
