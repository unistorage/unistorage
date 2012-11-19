import random

from app import fs
from tests.utils import StorageFunctionalTest, fixture_path


class FunctionalTest(StorageFunctionalTest):
    def get_random_type_id(self):
        hash = random.getrandbits(128)
        return '%032x' % hash

    def test(self):
        type_id = self.get_random_type_id()
        file_uri = self.put_file('./images/some.jpeg', type_id=type_id)
        file_id = self.get_id_from_uri(file_uri)
        self.assertEquals(fs.get(file_id).type_id, type_id)

    def test_too_long(self):
        type_id = self.get_random_type_id() + 'extracharacters'
        path = fixture_path('images/some.jpeg')
        response = self.app.post(
            '/', {'type_id': type_id}, upload_files=[('file', path)], status='*')
        self.assertEquals(response.json['status'], 'error')
        self.assertTrue('too long' in response.json['msg'])
