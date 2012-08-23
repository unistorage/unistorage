import unittest

from actions import validate_and_get_video_convert_args, ValidationError


class VideoConvertValidationTest(unittest.TestCase):
    def test(self):
        with self.assertRaisesRegexp(ValidationError, 'format must be specified'):
            validate_and_get_video_convert_args(None, {})
        
        with self.assertRaisesRegexp(ValidationError,
                'Video can be only converted to the one of following formats'):
            validate_and_get_video_convert_args(None, {'format': 'lalala'})
        
        with self.assertRaisesRegexp(ValidationError, 'vcodec must be specified'):
            validate_and_get_video_convert_args(None, {'format': 'flv'})

        with self.assertRaisesRegexp(ValidationError,
                'Format ogg allows only following video codecs'):
            validate_and_get_video_convert_args(None,
                    {'format': 'ogg', 'vcodec': 'divx', 'acodec': 'mp3'})

        with self.assertRaisesRegexp(ValidationError,
                'Format webm allows only following audio codecs'):
            validate_and_get_video_convert_args(None,
                    {'format': 'webm', 'vcodec': 'vp8', 'acodec': 'mp3'})
        
        r = validate_and_get_video_convert_args(None,
                {'format': 'mkv', 'vcodec': 'h264', 'acodec': 'mp3'})
        self.assertEquals(r, ['mkv', 'h264', 'mp3'])
        
        r = validate_and_get_video_convert_args(None, {'format': 'webm'})
        self.assertEquals(r, ['webm', 'vp8', 'vorbis'])
        
        r = validate_and_get_video_convert_args(None, {'format': 'ogg'})
        self.assertEquals(r, ['ogg', 'theora', 'vorbis'])
