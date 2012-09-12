import unittest
import logging.config

import yaml
from flask import g

from actions.images.resize import perform as resize
from actions.tasks import ActionException, perform_actions
from file_utils import get_content_type
from tests.utils import GridFSMixin, ContextMixin


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


class Test(ContextMixin, GridFSMixin, unittest.TestCase):
    def setUp(self):
        super(Test, self).setUp()
        # Mock logger
        self.handler = MockLoggingHandler(level=logging.ERROR)
        logger = logging.getLogger('action_error_logger')
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.addHandler(self.handler)

    def tearDown(self):
        super(Test, self).tearDown()
        # Restore logging configuration
        config = yaml.load(open('logging.conf'))
        logging.config.dictConfig(config)
    
    def test(self):
        """Tests that exception raised by action is logged"""
        path = './tests/images/some.jpeg'
        source_file = open(path, 'rb')

        # Make sure that exception raised
        with self.assertRaises(Exception):
            resize(source_file, 'keep', -123123, 0)

        source_id = self.put_file(path)
        target_id = g.fs.put('')

        # Make sure that it's logged
        self.assertEquals(len(self.handler.messages['error']), 0)
        perform_actions(source_id, target_id, {}, [('resize', ['keep', -123123, 0])])
        logged_message = self.handler.messages['error'][0]
        self.handler.reset()
        self.assertTrue('Action failed' in logged_message)
        self.assertTrue(str(source_id) in logged_message)
        self.assertTrue(str(target_id) in logged_message)
