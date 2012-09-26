import unittest

from actions.images import rotate
from actions.utils import ValidationError
from tests.utils import ContextMixin


class ValidationTest(ContextMixin, unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test(self):
        validate = rotate.validate_and_get_args

        with self.expect_validation_error('`angle` must be specified'):
            validate({})

        with self.expect_validation_error(
                'Unsupported `angle` value. Available values: 90, 180, 270.'):
            validate({'angle': '23'})
        
        with self.expect_validation_error(
                'Unsupported `angle` value. Available values: 90, 180, 270.'):
            validate({'angle': 'lalala'})
