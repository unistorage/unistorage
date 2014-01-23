# coding: utf-8
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        original_uri = self.put_file('images/some.jpeg')
       
        crop_action_url = '%s?action=crop&x1=20&y1=20&x2=70&y2=90' % original_uri
        r = self.app.get(crop_action_url)
        self.assertEquals(r.json['status'], 'ok')

        cropped_image_uri = r.json['resource_uri']
        
        self.run_worker()

        r = self.check(cropped_image_uri, width=50, height=70, mime='image/jpeg')

    def test_boundaries_validation(self):
        original_uri = self.put_file('images/some.jpeg')
       
        crop_action_url = '%s?action=crop&x1=20&y1=20&x2=7000&y2=9000' % original_uri
        r = self.app.get(crop_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], '`(x2, y2)` is out of the image boundaries.')
