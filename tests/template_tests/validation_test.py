import unittest

import actions.templates
from actions.utils import ValidationError


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)

    def test_presence_validation(self):
        validate = actions.templates.validate_and_get_template
        args = {
            'applicable_for': None,
            'actions': None,
        }
        with self.expect_validation_error('`applicable_for` is not specified'):
            validate(args)

        args['applicable_for'] = 'image'
        with self.expect_validation_error('`actions` must contain at least one action'):
            validate(args)

    def test_actions_validation(self):
        validate = actions.templates.validate_and_get_template
        args = {
            'applicable_for': 'image',
            'actions': [''],
        }
        with self.expect_validation_error('Error on step 1: action is not specified'):
            validate(args)

        args['actions'] = ['action=resize']
        with self.expect_validation_error('`mode` must be specified'):
            validate(args)

    def test_actions_compatibility_validation(self):
        validate = actions.templates.validate_and_get_template
        # First action (`convert` with `to` argument) applicable for both images and videos.
        # Since it preserves type family (converts video to video), second action must fail.
        with self.expect_validation_error('Error on step 2: action resize is not supported for video.'):
            validate({
                'applicable_for': 'video',
                'actions': ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'],
            })
