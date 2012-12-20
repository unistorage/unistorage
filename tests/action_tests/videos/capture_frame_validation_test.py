import unittest

from actions.videos import capture_frame
from actions.utils import ValidationError


class ValidationTest(unittest.TestCase):
    def expect_validation_error(self, error):
        return self.assertRaisesRegexp(ValidationError, error)
    
    def test_video_capture_frame_validation(self):
        validate = capture_frame.validate_and_get_args

        with self.expect_validation_error('`to` must be specified'):
            validate({})
        
        with self.expect_validation_error(
                'Frame can be only saved to the one of following formats'):
            validate({'to': 'lalala'})
        
        with self.expect_validation_error('`position` must be specified'):
            validate({'to': 'jpeg'}) 

        with self.expect_validation_error('`position` must be numeric value'):
            validate({'to': 'jpeg', 'position': 'asd'})

        r = validate({'to': 'jpeg', 'position': '2.0'})
        self.assertEquals(r, ['jpeg', 2.0])
