import os
import time
import unittest
from pprint import pprint

from bson.objectid import ObjectId
from webtest import TestApp

import settings
import app
import tests.utils


class FunctionalTest(unittest.TestCase, tests.utils.WorkerMixin):
    @classmethod
    def setUpClass(cls):
        cls.app = TestApp(app.app)
        cls.headers = {'Token': settings.TOKENS[0]}
        cls.db = app.get_mongodb_connection()[settings.MONGO_DB_NAME]
   
    def put_file(self, path):
        files = [('file', os.path.basename(path), open(path, 'rb').read())]
        r = self.app.post('/', headers=self.headers, upload_files=files)
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)
        return ObjectId(r.json['id'])

    def assert_mimetype(self, r, value):
        self.assertEquals(r.json['information']['mimetype'], value)

    def assert_fileinfo(self, r, key, value):
        self.assertEquals(r.json['information']['fileinfo'][key], value)

    def check(self, url, width=None, height=None, mime=None):
        r = self.app.get(url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        if width:
            self.assert_fileinfo(r, 'width', width)
        if height:
            self.assert_fileinfo(r, 'height', height)
        if mime:
            self.assert_mimetype(r, mime)
        return r
    
    def test_resize_keep_jpg(self):
        original_id = self.put_file('./tests/images/some.jpeg')

        url = '/%s/' % original_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        resize_action_url = url + '?action=resize&mode=keep&w=400'
        r = self.app.get(resize_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        resized_image_id = ObjectId(r.json['id'])

        resized_image_url = '/%s/' % resized_image_id
        r = self.app.get(resized_image_url, headers=self.headers)
        self.assertTrue('uri' in r.json)

        # Make sure that consequent calls return the same id for the same action
        r = self.app.get(resize_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')
        self.assertEquals(ObjectId(r.json['id']), resized_image_id)
        
        self.run_worker()
        # Make sure that original has resized image in modifications
        # and resized image points to it's original.
        resized_image = self.db.fs.files.find_one(resized_image_id)
        original_image = self.db.fs.files.find_one(original_id)
        self.assertEquals(resized_image['original'], original_id)
        self.assertTrue(resized_image_id in original_image['modifications'].values())

        r = self.check(resized_image_url, width=400, height=300, mime='image/jpeg')
        self.assertEquals(int(r.json['ttl']), settings.TTL)

    def test_convert_jpg_to_gif(self):
        original_id = self.put_file('./tests/images/some.jpeg')

        url = '/%s/' % original_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        convert_action_url = url + '?action=convert&to=gif'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_image_url = '/%s/' % r.json['id']
        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')

    def test_make_grayscale(self):
        original_id = self.put_file('./tests/images/some.png')

        url = '/%s/' % original_id
        self.check(url, width=43, height=43, mime='image/png')

        grayscale_action_url = url + '?action=make_grayscale'
        r = self.app.get(grayscale_action_url, headers=self.headers)
        
        self.run_worker()

        grayscaled_image_url = '/%s/' % r.json['id']
        self.check(grayscaled_image_url, width=43, height=43, mime='image/png')

    def test_validation_errors(self):
        original_id = self.put_file('./tests/docs/test.docx')

        url = '/%s/' % original_id

        r = self.app.get(url + '?action=lalala', headers=self.headers, status='*')
        self.assertEquals(r.json['status'], 'error')

        r = self.app.get(url + '?action=convert&to=lalala', headers=self.headers, status='*')
        self.assertEquals(r.json['status'], 'error')

    def test_convert_docx_to_html(self):
        original_id = self.put_file('./tests/docs/test.docx')

        url = '/%s/' % original_id
        r = self.app.get(url, headers=self.headers)
        self.check(url, mime='application/msword')
        
        convert_action_url = url + '?action=convert&to=html'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = '/%s/' % r.json['id']
        r = self.app.get(converted_doc_url, headers=self.headers)
        mimetype = r.json['information']['mimetype']
        self.assertTrue('xml' in mimetype or 'html' in mimetype)

    def test_convert_odt_to_pdf(self):
        original_id = self.put_file('./tests/docs/test.odt')

        url = '/%s/' % original_id
        self.check(url, mime='application/vnd.oasis.opendocument.text')
        
        convert_action_url = url + '?action=convert&to=pdf'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = '/%s/' % r.json['id']
        r = self.app.get(converted_doc_url, headers=self.headers)
        self.check(converted_doc_url, mime='application/pdf')

    def test_template(self):
        r = self.app.post('/create_template', {
            'applicable_for': 'image',
            'action[]': ['action=resize&mode=keep&w=400', 'action=make_grayscale']
        }, headers=self.headers)
        template_id = r.json['id']

        image_id = self.put_file('./tests/images/some.png')
        apply_template_url = '/%s/?template=%s' % (image_id, template_id)
        r = self.app.get(apply_template_url, headers=self.headers)

        self.assertEquals(r.json['status'], 'ok')

        video_id = self.put_file('./tests/videos/sample.3gp')
        apply_template_url = '/%s/?template=%s' % (video_id, template_id)
        r = self.app.get(apply_template_url, headers=self.headers, status='*')
        
        self.assertEquals(r.status_code, 400)
        self.assertTrue('not applicable' in r.json['msg'])
