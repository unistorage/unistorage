import os
import unittest
import logging

from converter import FFMpegConvertError
from PIL import Image
from gridfs import GridFS

import settings
import video_actions 
from image_actions import ImageMagickWrapper, PILWrapper, resize
from tasks import ActionException, perform_action
from connections import get_mongodb_connection


class MockLoggingHandler(logging.Handler):
    """Mock logging handler to check for expected logs."""
    def __init__(self, *args, **kwargs):
        self.reset()
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.messages[record.levelname.lower()].append(record.getMessage())

    def reset(self):
        self.messages = {
            'debug': [],
            'info': [],
            'warning': [],
            'error': [],
            'critical': [],
        }


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = get_mongodb_connection()[settings.MONGO_DB_NAME]
        cls.fs = GridFS(cls.db)
        # Mock logger
        cls.handler = MockLoggingHandler(level=logging.ERROR)
        logging.getLogger('action_error_logger').addHandler(cls.handler)

    def put_file(self, path):
        f = open(path, 'rb')
        filename = os.path.basename(path)
        return self.fs.put(f.read(), filename=filename)
    
    def test_imagemagick_wrapper(self):
        source_image = Image.open('./tests/images/some.jpeg')
        with self.assertRaises(ActionException):
            wrapper = ImageMagickWrapper(source_image)
            wrapper.resize(-123123, 0) # Bad arguments
            wrapper.finalize()

    def test_pil_wrapper(self):
        source_image = Image.open('./tests/images/some.jpeg')
        with self.assertRaises(Exception):
            wrapper = PILWrapper(source_image)
            wrapper.resize(-123123, 0) # Bad arguments
            wrapper.finalize()

    def test_video_convert(self):
        source_video = open('./tests/videos/sample.3gp')
        with self.assertRaises(FFMpegConvertError):
            video_actions.convert(source_video, 'webm', 'divx', 'mp3', # Incompatible codecs
                    only_try=True)

    def test_logging(self):
        path = './tests/images/some.jpeg'
        source_id = self.put_file(path)
        target_id = self.fs.put('')

        self.assertEquals(len(self.handler.messages['error']), 0)
        perform_action(source_id, target_id, {}, resize, ['mode', -10, -10])
        logged_message = self.handler.messages['error'][0]
        self.handler.reset()
        self.assertTrue('Action failed' in logged_message)
        self.assertTrue(str(source_id) in logged_message)
        self.assertTrue(str(target_id) in logged_message)
