import unittest

from actions.images import convert
from actions.utils import ValidationError
from tests.utils import ContextMixin


class ValidationTest(ContextMixin, unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test(self):
        validate = convert.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate({})

        with self.expect_validation_error('Source file can be only converted'):
            validate({'to': 'lalala'})
