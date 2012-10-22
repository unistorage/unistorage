from flask import url_for

import settings
from tests.utils import WorkerMixin, StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def assert_error(self, data, error):
        r = self.app.post(url_for('.zip_create'), data, status='*')
        self.assertEquals(r.json['status'], 'error')
        print error
        print r.json['msg']
        self.assertTrue(error in r.json['msg'])

    def test_validation(self):
        self.assert_error(
            {'filename': 'images.zip'},
            '`file[]` field is required and must contain at least one file URI.')

        self.assert_error(
            {'file_id': [], 'filename': 'images.zip'},
            '`file[]` field is required and must contain at least one file URI.')
        
        self.assert_error(
            {'file': ['123'], 'filename': 'images.zip'},
            'Not all `file[]` are correct file URIs.')

        file_uri = self.put_file('images/some.jpeg')
        self.assert_error(
            {'file': [file_uri]},
            '`filename` field is required.')

    def test(self):
        file1_uri = self.put_file('images/some.jpeg')
        file2_uri = self.put_file('images/some.png')
        file3_uri = self.put_file('images/some.gif')

        r = self.app.post(url_for('.zip_create'), {
            'file': [file1_uri, file2_uri, file3_uri],
            'filename': 'images.zip'
        })
        zip_resource_uri = r.json['resource_uri']

        r = self.app.get(zip_resource_uri)
        self.assertTrue(settings.UNISTORE_NGINX_SERVE_URL in r.json['information']['uri'])
