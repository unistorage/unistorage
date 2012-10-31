from tests.utils import StorageFunctionalTest


class ValidationTest(StorageFunctionalTest):
    def test_unsupported_codecs_validation(self):
        source_uri = self.put_file('unsupported_videos/29.wmv')
        watermark_uri = self.put_file('watermarks/watermark.png')
        
        watermark_action_url = '%s?action=watermark&watermark=%s' \
                               '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % \
                               (source_uri, watermark_uri)
        r = self.app.get(watermark_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'Sorry, we can\'t handle video stream encoded using wmv3')

