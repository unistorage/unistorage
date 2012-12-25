import random

from app import fs
from tests.utils import StorageFunctionalTest, fixture_path


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        file_uri = self.put_file('./images/broken/1.jpg')
        response = self.app.get(file_uri).json
        self.assertEquals(response['data']['unistorage_type'], 'unknown')
