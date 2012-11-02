from flask import g

import settings
from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_uri = self.put_file('images/some.jpeg')
        original_id = self.get_id_from_uri(original_uri)
        self.check(original_uri, width=640, height=480, mime='image/jpeg')
        
        resize_action_url = '%s?action=resize&mode=keep&w=400' % original_uri
        r = self.app.get(resize_action_url)
        self.assertEquals(r.json['status'], 'ok')

        resized_image_uri = r.json['resource_uri']
        resized_image_id = self.get_id_from_uri(resized_image_uri)

        r = self.app.get(resized_image_uri)
        self.assertTrue('url' in r.json['data'])

        # Make sure that consequent calls return the same id for the same action
        r = self.app.get(resize_action_url)
        self.assertEquals(r.json['status'], 'ok')
        self.assertEquals(
            self.get_id_from_uri(r.json['resource_uri']),
            resized_image_id)
        
        self.run_worker()
        # Make sure that original has resized image in modifications
        # and resized image points to it's original.
        resized_image = g.db.fs.files.find_one(resized_image_id)
        original_image = g.db.fs.files.find_one(original_id)
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        r = self.check(resized_image_uri, width=400, height=300, mime='image/jpeg')
        self.assertEquals(int(r.json['ttl']), settings.TTL)

    def test_validation_errors(self):
        uri = self.put_file('images/some.jpeg')

        r = self.app.get(uri + '?action=lalala', status='*')
        self.assertEquals(r.json['status'], 'error')

        r = self.app.get(uri + '?action=convert&to=lalala', status='*')
        self.assertEquals(r.json['status'], 'error')
