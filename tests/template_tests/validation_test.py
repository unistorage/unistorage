import unittest

import actions.templates
from actions.utils import ValidationError


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def test_presence_validation(self):
        validate = actions.templates.validate_and_get_template
        with self.expect_validation_error('`applicable_for` is not specified'):
            validate([], '')

        with self.expect_validation_error('`actions` must contain at least one action'):
            validate(['image'], [])

    def test_actions_validation(self):
        validate = actions.templates.validate_and_get_template
        applicable_for = 'image'
        with self.expect_validation_error('Error on step 1: action is not specified'):
            validate(applicable_for, [''])

        with self.expect_validation_error('`mode` must be specified'):
            validate(applicable_for, ['action=resize'])

    def test_actions_compatibility(self):
        validate = actions.templates.validate_and_get_template
        # First action (`convert` with `to` argument) applicable for both images and videos.
        # Since it preserves type family (converts video to video), second action must fail.
        with self.expect_validation_error('Error on step 2: action resize is not supported for video.'):
            validate('video', ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'])
