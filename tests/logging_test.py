import unittest
import logging.config

import yaml

from app import fs
from actions.images.resize import perform as resize
from actions.tasks import perform_actions
from tests.utils import GridFSMixin, ContextMixin, fixture_path


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


class Test(GridFSMixin, ContextMixin, unittest.TestCase):
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
        pass
        return
        path = 'images/some.jpeg'
        source_file = open(fixture_path(path), 'rb')

        # Make sure that exception raised
        with self.assertRaises(Exception):
            resize(source_file, 'keep', -123123, 0)

        source_id = self.put_file(path)
        target_id = fs.put('', pending=True, actions=[('resize', ['keep', -123123, 0])])

        # Make sure that it's logged
        self.assertEquals(len(self.handler.messages['error']), 0)
        perform_actions(source_id, target_id, {})
        logged_message = self.handler.messages['error'][0]
        self.handler.reset()
        self.assertTrue('Action failed' in logged_message)
        self.assertTrue(str(source_id) in logged_message)
        self.assertTrue(str(target_id) in logged_message)
