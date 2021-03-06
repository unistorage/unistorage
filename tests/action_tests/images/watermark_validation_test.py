import unittest

from flask import url_for

from actions.images import watermark
from actions.utils import ValidationError
from tests.utils import ContextMixin, GridFSMixin


class ValidationTest(GridFSMixin, ContextMixin, unittest.TestCase):
    def setUp(self):
        super(ValidationTest, self).setUp()
        self.watermark_id = self.put_file('watermarks/watermark.png')
        self.watermark_uri = url_for('storage.file_view', _id=self.watermark_id)

        self.file_id = self.put_file('docs/test.docx')
        self.file_uri = url_for('storage.file_view', _id=self.file_id)
    
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def get_valid_args(self):
        return {
            'watermark': self.watermark_uri,
            'w': '45px',
            'h': '30',
            'w_pad': '10px',
            'h_pad': '5',
            'corner': 'ne'
        }
    
    def test(self):
        validate = watermark.validate_and_get_args

        with self.expect_validation_error('must be specified'):
            validate({})
        
        args = self.get_valid_args()
        del args['w_pad']
        with self.expect_validation_error('`w_pad` must be specified'):
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
        inexistent_watermark_id = 'abcde' + str(self.watermark_id)[5:]
        inexistent_watermark_uri = url_for('storage.file_view', _id=inexistent_watermark_id)
        args.update({'watermark': inexistent_watermark_uri})
        with self.expect_validation_error('File with id %s does not exist.' % inexistent_watermark_id):
            validate(args)

        args = self.get_valid_args()
        corrupted_watermark_uri = '/asdasdas213124'
        args.update({'watermark': corrupted_watermark_uri})
        with self.expect_validation_error('%s is not a file URI.' % corrupted_watermark_uri):
            validate(args)

        args = self.get_valid_args()
        args.update({'watermark': self.file_uri})
        with self.expect_validation_error('File with id %s is not an image.' % self.file_id):
            validate(args)

        args = self.get_valid_args()
        self.assertEquals(validate(args), [self.watermark_id, 45, 0.3, 10, 0.05, 'ne'])
