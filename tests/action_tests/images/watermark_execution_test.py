import unittest

from flask import g

from actions.images import watermark
from actions.utils import ValidationError
from tests.utils import ContextMixin, GridFSMixin


class ExecutionTest(ContextMixin, GridFSMixin, unittest.TestCase):
    def setUp(self):
        super(ExecutionTest, self).setUp()
        self.watermark_id = str(self.put_file('./tests/watermarks/watermark.png'))
    
    def test(self):
        source_id = self.put_file('./tests/images/some.jpeg')
        w = h = 5
        hpad = vpad = 5
        corner = 'ne'
        result_data, result_extension = watermark.perform(g.fs.get(source_id),
                self.watermark_id, w, h, hpad, vpad, corner)

        self.assertEquals(watermark.identify(result_data, '%wx%h'), '640x480')
        self.assertTrue(result_extension in ('jpeg', 'jpg'))
