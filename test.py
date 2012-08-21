import sys
import time
import unittest
from pprint import pprint

from bson.objectid import ObjectId
from rq import Queue
import requests
import gridfs

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
        self.fs = gridfs.GridFS(self.db)

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
        original_id = self.put_file('./test_images/some.jpeg')

        url = '%s/%s/' % (self.base_url, original_id)
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        resize_action_url = url + '?action=resize&mode=keep&w=400'
        r = requests.get(resize_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        resized_image_id = ObjectId(r.json['id'])

        resized_image_url = '%s/%s/' % (self.base_url, resized_image_id)
        r = requests.get(resized_image_url, headers=self.headers)
        self.assertTrue('finish_time' in r.json)

        # Make sure that consequent calls return the same id for the same action
        r = requests.get(resize_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertEquals(ObjectId(r.json['id']), resized_image_id)
        
        time.sleep(.5)
        # Make sure that original has resized image in modifications
        # and resized image points to it's original.
        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        r = self.check(resized_image_url, width=400, height=300, mime='image/jpeg')
        self.assertTrue('finish_time' not in r.json)

    def test_convert_jpg_to_gif(self):
        original_id = self.put_file('./test_images/some.jpeg')

        url = '%s/%s/' % (self.base_url, original_id)
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        convert_action_url = url + '?action=convert&to=image/gif'
        r = requests.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        time.sleep(.5)

        converted_image_url = '%s/%s/' % (self.base_url, r.json['id'])
        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')
        self.assertTrue('finish_time' not in r.json)

    def test_make_grayscale(self):
        original_id = self.put_file('./test_images/some.png')

        url = '%s/%s/' % (self.base_url, original_id)
        self.check(url, width=43, height=43, mime='image/png')

        grayscale_action_url = url + '?action=make_grayscale'
        r = requests.get(grayscale_action_url, headers=self.headers)
        
        time.sleep(.5)

        grayscaled_image_url = '%s/%s/' % (self.base_url, r.json['id'])
        self.check(grayscaled_image_url, width=43, height=43, mime='image/png')

    def test_validation_errors(self):
        original_id = self.put_file('./test_images/some.png')

        url = '%s/%s/' % (self.base_url, original_id)

        r = requests.get(url + '?action=lalala', headers=self.headers)
        self.assertEquals(r.json['status'], 'error')

        r = requests.get(url + '?action=convert&to=lalala', headers=self.headers)
        self.assertEquals(r.json['status'], 'error')

if __name__ == '__main__':
    unittest.main()
