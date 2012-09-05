import os
import unittest
import logging.config

import yaml
from converter import FFMpegConvertError
from PIL import Image
from gridfs import GridFS

import settings
from actions.images.resize import perform as resize
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
        logger = logging.getLogger('action_error_logger')
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.addHandler(cls.handler)

    @classmethod
    def tearDownClass(cls):
        # Restore logging configuration
        config = yaml.load(open('logging.conf'))
        logging.config.dictConfig(config)

    def put_file(self, path):
        f = open(path, 'rb')
        filename = os.path.basename(path)
        return self.fs.put(f.read(), filename=filename)
    
    def test_imagemagick_wrapper(self):
        """Tests that exception raised by action is logged"""
        path = './tests/images/some.jpeg'
        source_file = open(path, 'rb')

        # Make sure that exception raised
        with self.assertRaises(Exception):
            resize(source_file, 'keep', -123123, 0)

        source_id = self.put_file(path)
        target_id = self.fs.put('')

        # Make sure that it's logged
        self.assertEquals(len(self.handler.messages['error']), 0)
        perform_action(source_id, target_id, {}, resize, ['keep', -123123, 0])
        logged_message = self.handler.messages['error'][0]
        self.handler.reset()
        self.assertTrue('Action failed' in logged_message)
        self.assertTrue(str(source_id) in logged_message)
        self.assertTrue(str(target_id) in logged_message)
