import unittest

import actions.videos
import actions.docs
import actions.images
from actions.utils import ValidationError

class FileMock(object):
    def __init__(self, content_type=None):
        self.content_type = content_type


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test_doc_convert_validation(self):
        source_file = FileMock(content_type='application/msword')
        validate = actions.docs.convert.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate(source_file, {})

        with self.expect_validation_error(
                'Source file is %s and can be only converted' % source_file.content_type):
            validate(source_file, {'to': 'gif'})

    def test_image_convert_validation(self):
        source_file = FileMock(content_type='image/jpeg')
        validate = actions.images.convert.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate(source_file, {})

        with self.expect_validation_error(
                'Source file is %s and can be only converted' % source_file.content_type):
            actions.docs.convert.validate_and_get_args(source_file, {'to': 'gif'})

    def test_video_convert_validation(self):
        source_file = FileMock(content_type='video/webm')
        validate = actions.videos.convert.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate(source_file, {})
        
        with self.expect_validation_error(
                'Source file is video/webm and can be only converted to the one of following formats'):
            validate(source_file, {'to': 'lalala'})
        
        with self.expect_validation_error('vcodec must be specified'):
            validate(source_file, {'to': 'flv'})

        with self.expect_validation_error(
                'Format ogg allows only following video codecs'):
            validate(source_file,
                    {'to': 'ogg', 'vcodec': 'divx', 'acodec': 'mp3'})

        with self.expect_validation_error(
                'Format webm allows only following audio codecs'):
            validate(source_file,
                    {'to': 'webm', 'vcodec': 'vp8', 'acodec': 'mp3'})
        
        r = validate(source_file,
                {'to': 'mkv', 'vcodec': 'h264', 'acodec': 'mp3'})
        self.assertEquals(r, ['mkv', 'h264', 'mp3'])
        
        r = validate(source_file, {'to': 'webm'})
        self.assertEquals(r, ['webm', 'vp8', 'vorbis'])
        
        r = validate(source_file, {'to': 'ogg'})
        self.assertEquals(r, ['ogg', 'theora', 'vorbis'])
