from flask import g
from bson.objectid import ObjectId

import settings
from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_id = self.put_file('images/some.jpeg')

        url = '/%s/' % original_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        resize_action_url = url + '?action=resize&mode=keep&w=400'
        r = self.app.get(resize_action_url)
        self.assertEquals(r.json['status'], 'ok')
        resized_image_id = ObjectId(r.json['id'])

        resized_image_url = '/%s/' % resized_image_id
        r = self.app.get(resized_image_url)
        self.assertTrue('uri' in r.json)

        # Make sure that consequent calls return the same id for the same action
        r = self.app.get(resize_action_url)
        self.assertEquals(r.json['status'], 'ok')
        self.assertEquals(ObjectId(r.json['id']), resized_image_id)
        
        self.run_worker()
        # Make sure that original has resized image in modifications
        # and resized image points to it's original.
        resized_image = g.db.fs.files.find_one(resized_image_id)
        original_image = g.db.fs.files.find_one(original_id)
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        r = self.check(resized_image_url, width=400, height=300, mime='image/jpeg')
        self.assertEquals(int(r.json['ttl']), settings.TTL)

    def test_validation_errors(self):
        original_id = self.put_file('images/some.jpeg')

        url = '/%s/' % original_id

        r = self.app.get(url + '?action=lalala', status='*')
        self.assertEquals(r.json['status'], 'error')

        r = self.app.get(url + '?action=convert&to=lalala', status='*')
        self.assertEquals(r.json['status'], 'error')
