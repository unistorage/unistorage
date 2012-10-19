from flask import url_for

import settings
from tests.utils import WorkerMixin, StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def assert_error(self, data, error):
        r = self.app.post(url_for('.create_zip_view'), data, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertTrue(error in r.json['msg'])

    def test_validation(self):
        self.assert_error(
            {'filename': 'images.zip'},
            '`file_id[]` field is required and must contain at least one id.')

        self.assert_error(
            {'file_id': [], 'filename': 'images.zip'},
            '`file_id[]` field is required and must contain at least one id.')
        
        self.assert_error(
            {'file_id': ['123'], 'filename': 'images.zip'},
            'Not all `file_id[]` are correct identifiers')

        file1_id = self.put_file('images/some.jpeg')
        self.assert_error(
            {'file_id': [file1_id]},
            '`filename` field is required.')

    def test(self):
        _, file1_id = self.put_file('images/some.jpeg')
        _, file2_id = self.put_file('images/some.png')
        _, file3_id = self.put_file('images/some.gif')

        r = self.app.post(url_for('.create_zip_view'), {
            'file_id': [file1_id, file2_id, file3_id],
            'filename': 'images.zip'
        })
        zip_resource_uri = r.json['resource_uri']

        r = self.app.get(zip_resource_uri)
        self.assertTrue(settings.UNISTORE_NGINX_SERVE_URL in r.json['information']['uri'])
