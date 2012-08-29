import unittest

from actions import validate_and_get_video_convert_args, \
        validate_and_get_image_convert_args, \
        validate_and_get_doc_convert_args, ValidationError


class FileMock(object):
    def __init__(self, content_type=None):
        self.content_type = content_type


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test_doc_convert_validation(self):
        source_file = FileMock(content_type='application/msword')
        with self.expect_validation_error('`to` must be specified'):
            validate_and_get_doc_convert_args(source_file, {})

        with self.expect_validation_error(
                'Source file is %s and can be only converted' % source_file.content_type):
            validate_and_get_doc_convert_args(source_file, {'to': 'gif'})

    def test_image_convert_validation(self):
        source_file = FileMock(content_type='image/jpeg')
        with self.expect_validation_error('`to` must be specified'):
            validate_and_get_image_convert_args(source_file, {})

        with self.expect_validation_error(
                'Source file is %s and can be only converted' % source_file.content_type):
            validate_and_get_doc_convert_args(source_file, {'to': 'gif'})

    def test_video_convert_validation(self):
        source_file = FileMock(content_type='video/webm')

        with self.expect_validation_error('`to` must be specified'):
            validate_and_get_video_convert_args(source_file, {})
        
        with self.expect_validation_error(
                'Source file is video/webm and can be only converted to the one of following formats'):
            validate_and_get_video_convert_args(source_file, {'to': 'lalala'})
        
        with self.expect_validation_error('vcodec must be specified'):
            validate_and_get_video_convert_args(source_file, {'to': 'flv'})

        with self.expect_validation_error(
                'Format ogg allows only following video codecs'):
            validate_and_get_video_convert_args(source_file,
                    {'to': 'ogg', 'vcodec': 'divx', 'acodec': 'mp3'})

        with self.expect_validation_error(
                'Format webm allows only following audio codecs'):
            validate_and_get_video_convert_args(source_file,
                    {'to': 'webm', 'vcodec': 'vp8', 'acodec': 'mp3'})
        
        r = validate_and_get_video_convert_args(source_file,
                {'to': 'mkv', 'vcodec': 'h264', 'acodec': 'mp3'})
        self.assertEquals(r, ['mkv', 'h264', 'mp3'])
        
        r = validate_and_get_video_convert_args(source_file, {'to': 'webm'})
        self.assertEquals(r, ['webm', 'vp8', 'vorbis'])
        
        r = validate_and_get_video_convert_args(source_file, {'to': 'ogg'})
        self.assertEquals(r, ['ogg', 'theora', 'vorbis'])
