import unittest

from actions.images import resize
from actions.utils import ValidationError
from tests.utils import ContextMixin


class ValidationTest(ContextMixin, unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def get_valid_args(self):
        return {
            'mode': 'keep',
            'w': '500'
        }

    def test(self):
        validate = resize.validate_and_get_args

        with self.expect_validation_error('must be specified'):
            validate({})

        args = self.get_valid_args()
        del args['mode']
        with self.expect_validation_error('`mode` must be specified'):
            validate(args)

        args = self.get_valid_args()
        args.update({'mode': 'lalala'})
        with self.expect_validation_error('Unknown `mode`'):
            validate(args)

        args = self.get_valid_args()
        args.update({'w': 'bububu'})
        with self.expect_validation_error('`w` and `h` must be integer values'):
            validate(args)

        args = self.get_valid_args()
        args.update({'mode': 'resize'})
        with self.expect_validation_error('Both `w` and `h` must be specified'):
            validate(args)

        args = self.get_valid_args()
        self.assertEquals(validate(args), ['keep', 500, None])
