import unittest

from actions.images import crop
from actions.utils import ValidationError


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def get_valid_args(self):
        return {
            'x': '50',
            'y': '50',
            'w': '40',
            'h': '70',
        }

    def test(self):
        validate = crop.validate_and_get_args

        with self.expect_validation_error('must be specified'):
            validate({})

        args = self.get_valid_args()
        del args['x']
        with self.expect_validation_error('`x` must be specified'):
            validate(args)

        args = self.get_valid_args()
        args.update({'x': 'bububu'})
        with self.expect_validation_error('must be integer values'):
            validate(args)

        args = self.get_valid_args()
        args.update({'y': '-1'})
        with self.expect_validation_error('must be positive integer values'):
            validate(args)

        args = self.get_valid_args()
        validate(args)
