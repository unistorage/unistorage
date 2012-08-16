import sys
import time
import unittest
from pprint import pprint

from bson.objectid import ObjectId
from rq import Queue
import requests

import settings
import app


class Test(unittest.TestCase):
    def setUp(self):
        try:
            port = int(sys.argv[1])
        except:
            port = 5000

        self.base_url = 'http://127.0.0.1:%d' % port
        self.headers = {'Token': settings.TOKENS[0]}
        self.db = app.get_mongodb_connection()[settings.MONGO_DB_NAME]
        self.q = Queue(connection=app.get_redis_connection())

    def _put_file(self, path):
        files = {'file': open(path, 'rb')}
        r = requests.post(self.base_url, files=files, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)

        return ObjectId(r.json['id'])

    def assert_mimetype(self, r, value):
        self.assertEquals(r.json['information']['mimetype'], value)

    def assert_fileinfo(self, r, key, value):
        self.assertEquals(r.json['information']['fileinfo'][key], value)
    
    def test_resize_keep_jpg(self):
        original_id = self._put_file('./fixtures/some.jpg')

        url = '%s/%s/' % (self.base_url, original_id)
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assert_mimetype(r, 'image/jpeg')
        self.assert_fileinfo(r, 'width', 640)
        self.assert_fileinfo(r, 'height', 480)

        url = url + '?action=resize&mode=keep&w=400'
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertFalse('information' in r.json)
        
        resized_image_id = ObjectId(r.json['id'])
        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)
        
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'])
        
        time.sleep(1)
        url = '%s/%s/' % (self.base_url, resized_image_id)
        r = requests.get(url, headers=self.headers)
        self.assert_mimetype(r, 'image/jpeg')
        self.assert_fileinfo(r, 'width', 400)
        self.assert_fileinfo(r, 'height', 300)

    def test_resize_crop_gif(self):
        original_id = self._put_file('./fixtures/animated2.gif')

        url = '%s/%s/' % (self.base_url, original_id)
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assert_mimetype(r, 'image/gif')
        self.assert_fileinfo(r, 'width', 410)
        self.assert_fileinfo(r, 'height', 299)

        url = url + '?action=resize&mode=crop&w=200&h=200'
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertFalse('information' in r.json)
        
        resized_image_id = ObjectId(r.json['id'])
        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)
        
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'])
        
        time.sleep(10)
        url = '%s/%s/' % (self.base_url, resized_image_id)
        r = requests.get(url, headers=self.headers)
        self.assert_mimetype(r, 'image/gif')
        self.assert_fileinfo(r, 'width', 200)
        self.assert_fileinfo(r, 'height', 200)

if __name__ == '__main__':
    unittest.main()
