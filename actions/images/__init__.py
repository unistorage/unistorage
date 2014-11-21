# coding: utf-8
import subprocess
from cStringIO import StringIO

import settings
from identify import identify_file
from actions.utils import ActionError


class ImageMagickWrapper(object):
    def __init__(self, image):
        self._image = image
        image_data = identify_file(image)
        self._is_animated = image_data['is_animated']
        self._format = image_data['format'].upper()
        self._args = []
        self._common_args = [settings.CONVERT_BIN]

    def make_grayscale(self):
        self._args.extend(['-colorspace', 'gray'])
        return self

    def resize(self, width, height):
        self._args.extend(['-resize', '%dx%d!' % (width, height)])
        if self._format == 'JPEG':
            # Параметр jpeg:size оптимизирует расход ресурсов, актуален только для ресайза
            # Ресайз в рамках системы используется один раз для одного файла
            self._common_args.extend(['-define', 'jpeg:size={}x{}'.format(width, height)])
        return self

    def rotate(self, angle):
        # 360 - angle, т.к. imagemagick поворачивает по часовой
        self._args.extend(['-rotate', str(-angle)])
        return self

    def strip_exif(self):
        self._args.extend(['-strip'])
        return self

    def auto_orient(self):
        self._args.extend(['-auto-orient'])
        return self

    def crop(self, x, y, w, h):
        self._args.extend(['-crop', '%dx%d+%d+%d' % (w, h, x, y), '+repage'])
        return self

    def crop_to_center(self, width, height):
        self._args.extend(['-gravity', 'Center',
                           '-crop', '%dx%d+0+0' % (width, height), '+repage'])
        return self

    def finalize(self, **kwargs):
        format = kwargs.get('format', self._format).upper()

        self._common_args.append('-')
        if self._is_animated and format != self._format:
            # If converting from animated image to static, specify frame number
            self._common_args[-1] += '[0]'
        else:
            self._common_args.append('-coalesce')

        self._args.append('%s:-' % format.upper())
        self._common_args.extend(self._args)

        proc_input = self._image
        proc_input.seek(0)
        try:
            proc = subprocess.Popen(self._common_args, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise ActionError('Failed to start ImageMagick\'s convert: %s' % self._args[0])

        result, error = proc.communicate(input=proc_input.read())
        return_code = proc.wait()
        if return_code != 0:
            raise ActionError(
                'ImageMagick\'s convert (%s) failed: %s' % (self._args[0], error))

        return StringIO(result), format.lower()
