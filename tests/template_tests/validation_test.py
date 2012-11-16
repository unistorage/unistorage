import unittest

import actions.templates
from app import fs
from actions.handlers import apply_template
from actions.utils import ValidationError
from tests.utils import ContextMixin, GridFSMixin


class ValidationTest(GridFSMixin, ContextMixin, unittest.TestCase):
    def setUp(self):
        super(ValidationTest, self).setUp()
        self.file_id = self.put_file('images/some.jpeg')

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
        with self.expect_validation_error('Error on step 2: action resize is '
                                          'not supported for video.'):
            validate({
                'applicable_for': 'video',
                'actions': ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'],
            })

    def test_apply_template_uri_validation(self):
        corrupted_template_uri = '/template/asds123'
        with self.expect_validation_error('%s is not a template URI.' % corrupted_template_uri):
            apply_template(fs.get(self.file_id), {'template': corrupted_template_uri})

        inexistent_template_id = '5087a78f8149954b38d1cbc2'
        inexistent_template_uri = '/template/%s/' % inexistent_template_id
        with self.expect_validation_error(
                'Template with id %s does not exist.' % inexistent_template_id):
            apply_template(fs.get(self.file_id), {'template': inexistent_template_uri})
