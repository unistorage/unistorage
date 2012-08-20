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

    def put_file(self, path):
        files = {'file': open(path, 'rb')}
        r = requests.post(self.base_url, files=files, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)

        return ObjectId(r.json['id'])

    def assert_mimetype(self, r, value):
        self.assertEquals(r.json['information']['mimetype'], value)

    def assert_fileinfo(self, r, key, value):
        self.assertEquals(r.json['information']['fileinfo'][key], value)

    def check(self, url, width=None, height=None, mime=None):
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        if width:
            self.assert_fileinfo(r, 'width', width)
        if height:
            self.assert_fileinfo(r, 'height', height)
        if mime:
            self.assert_mimetype(r, mime)
        return r
    
    def test_resize_keep_jpg(self):
        original_id = self.put_file('./test_images/some.jpg')

        url = '%s/%s/' % (self.base_url, original_id)
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        resize_url = url + '?action=resize&mode=keep&w=400'
        r = requests.get(resize_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        resized_image_id = ObjectId(r.json['id'])

        url = '%s/%s/' % (self.base_url, resized_image_id)
        r = requests.get(url, headers=self.headers)
        self.assertTrue('finish_time' in r.json)

        # Make sure that consequent calls return the same id for the same action
        r = requests.get(resize_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertEquals(ObjectId(r.json['id']), resized_image_id)
        
        time.sleep(1)
        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)

        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        url = '%s/%s/' % (self.base_url, resized_image_id)
        r = self.check(url, width=400, height=300, mime='image/jpeg')
        self.assertTrue('finish_time' not in r.json)

    def test_resize_crop_gif(self):
        original_id = self.put_file('./test_images/animated.gif')

        url = '%s/%s/' % (self.base_url, original_id)
        self.check(url, width=410, height=299, mime='image/gif')

        url = url + '?action=resize&mode=crop&w=200&h=200'
        r = requests.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        resized_image_id = ObjectId(r.json['id'])

        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)
        
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        time.sleep(10)
        url = '%s/%s/' % (self.base_url, resized_image_id)
        r = requests.get(url, headers=self.headers)
        self.check(url, width=200, height=200, mime='image/gif')

    def test_make_grayscale(self):
        original_id = self.put_file('./test_images/some.png')

        url = '%s/%s/' % (self.base_url, original_id)
        r = requests.get(url, headers=self.headers)
        self.check(url, width=43, height=43, mime='image/png')

        url = url + '?action=make_grayscale'
        r = requests.get(url, headers=self.headers)
        
        time.sleep(1)
        url = '%s/%s/' % (self.base_url, r.json['id'])
        self.check(url, width=43, height=43, mime='image/png')

if __name__ == '__main__':
    unittest.main()
