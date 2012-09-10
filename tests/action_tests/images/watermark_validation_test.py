import os
import unittest

from flask import g

import app
import fileutils
from actions.images import watermark
from actions.utils import ValidationError
from tests.utils import ContextMixin


class ValidationTest(ContextMixin, unittest.TestCase):
    def setUp(self):
        super(ValidationTest, self).setUp()
        self.watermark_id = self.put_file('./tests/watermarks/watermark.png')

    def put_file(self, path):
        f = open(path, 'rb')
        filename = os.path.basename(path)
        content_type = fileutils.get_content_type(f)
        return g.fs.put(f.read(), filename=filename, content_type=content_type)

    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def get_valid_args(self):
        return {
            'watermark_id': self.watermark_id,
            'w': '45px',
            'h': '30',
            'h_pad': '10px',
            'v_pad': '5',
            'corner': 'ne'
        }
    
    def test(self):
        validate = watermark.validate_and_get_args

        with self.expect_validation_error('must be specified'):
            validate({})
        
        args = self.get_valid_args()
        del args['h_pad']
        with self.expect_validation_error('`h_pad` must be specified'):
            validate(args)

        args = self.get_valid_args()
        args.update({'w': 'bububu'})
        with self.expect_validation_error('`w` must be an integer'):
            validate(args)
        
        args = self.get_valid_args()
        args.update({'w': '120'})
        with self.expect_validation_error('Percent value `w` must be between 0 and 100'):
            validate(args)

        args = self.get_valid_args()
        args.update({'corner': 'lalala'})
        with self.expect_validation_error('`corner` must be one of the following: ne, se, sw, nw'):
            validate(args)

        args = self.get_valid_args()
        self.assertEquals(validate(args), [self.watermark_id, 45, 0.3, 10, 0.05, 'ne'])
