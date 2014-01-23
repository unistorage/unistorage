import unittest

from actions.images import crop
from actions.utils import ValidationError


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def get_valid_args(self):
        return {
            'x1': '50',
            'y1': '50',
            'x2': '90',
            'y2': '120',
        }

    def test(self):
        validate = crop.validate_and_get_args

        with self.expect_validation_error('must be specified'):
            validate({})

        args = self.get_valid_args()
        del args['x1']
        with self.expect_validation_error('`x1` must be specified'):
            validate(args)

        args = self.get_valid_args()
        args.update({'x2': 'bububu'})
        with self.expect_validation_error('must be integer values'):
            validate(args)

        args = self.get_valid_args()
        args.update({'y1': '-1'})
        with self.expect_validation_error('must be positive integer values'):
            validate(args)

        args = self.get_valid_args()
        args.update({'x1': '100', 'x2': '10'})
        with self.expect_validation_error('`x1` must be strictly less than `x2`.'):
            validate(args)

        args = self.get_valid_args()
        args.update({'y1': '100', 'y2': '10'})
        with self.expect_validation_error('`y1` must be strictly less than `y2`.'):
            validate(args)

        args = self.get_valid_args()
        validate(args)
