import unittest

from actions.videos import convert
from actions.utils import ValidationError
from tests.utils import ContextMixin


class ValidationTest(ContextMixin, unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test_video_convert_validation(self):
        validate = convert.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate({})
        
        with self.expect_validation_error(
                'Source file can be only converted to the one of following formats'):
            validate({'to': 'lalala'})
        
        with self.expect_validation_error('vcodec must be specified'):
            validate({'to': 'flv'})

        with self.expect_validation_error(
                'Format ogg allows only following video codecs'):
            validate({'to': 'ogg', 'vcodec': 'divx', 'acodec': 'mp3'})

        with self.expect_validation_error(
                'Format webm allows only following audio codecs'):
            validate({'to': 'webm', 'vcodec': 'vp8', 'acodec': 'mp3'})
        
        r = validate({'to': 'mkv', 'vcodec': 'h264', 'acodec': 'mp3'})
        self.assertEquals(r, ['mkv', 'h264', 'mp3'])
        
        r = validate({'to': 'webm'})
        self.assertEquals(r, ['webm', 'vp8', 'vorbis'])
        
        r = validate({'to': 'ogg'})
        self.assertEquals(r, ['ogg', 'theora', 'vorbis'])
