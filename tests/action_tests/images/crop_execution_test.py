# coding: utf-8
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        original_uri = self.put_file('images/some.jpeg')

        crop_action_url = '%s?action=crop&x1=20&y1=20&x2=69&y2=21' % original_uri
        r = self.app.get(crop_action_url)
        self.assertEquals(r.json['status'], 'ok')
        cropped_image_uri = r.json['resource_uri']

        self.run_worker()
        r = self.check(cropped_image_uri, width=50, height=2, mime='image/jpeg')

        crop_action_url = '%s?action=crop&x1=0&y1=0&x2=639&y2=479' % original_uri
        r = self.app.get(crop_action_url)
        self.assertEquals(r.json['status'], 'ok')
        cropped_image_uri = r.json['resource_uri']

        self.run_worker()
        r = self.check(cropped_image_uri, width=640, height=480, mime='image/jpeg')

    def test_boundaries_validation(self):
        original_uri = self.put_file('images/some.jpeg')
        self.check(original_uri, width=640, height=480, mime='image/jpeg')

        crop_action_url = '%s?action=crop&x1=20&y1=20&x2=640&y2=479' % original_uri
        r = self.app.get(crop_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], '`(x2, y2)` is out of the image boundaries.')
