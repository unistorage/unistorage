# coding: utf-8
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        original_uri = self.put_file('images/some.jpeg')

        crop_action_url = '%s?action=crop&x=20&y=20&w=50&h=2' % original_uri
        r = self.app.get(crop_action_url)
        self.assertEquals(r.json['status'], 'ok')
        cropped_image_uri = r.json['resource_uri']

        self.run_worker()
        r = self.check(cropped_image_uri, width=50, height=2, mime='image/jpeg')

        crop_action_url = '%s?action=crop&x=0&y=0&w=640&h=480' % original_uri
        r = self.app.get(crop_action_url)
        self.assertEquals(r.json['status'], 'ok')
        cropped_image_uri = r.json['resource_uri']

        self.run_worker()
        r = self.check(cropped_image_uri, width=640, height=480, mime='image/jpeg')

    def test_boundaries_validation(self):
        original_uri = self.put_file('images/some.jpeg')
        self.check(original_uri, width=640, height=480, mime='image/jpeg')

        crop_action_url = '%s?action=crop&x=20&y=20&w=639&h=481' % original_uri
        r = self.app.get(crop_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'The crop region is out of the image boundaries.')
