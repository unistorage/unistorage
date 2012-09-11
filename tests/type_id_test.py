import random

from flask import g

from tests.utils import FunctionalTest, ContextMixin


class FunctionalTest(ContextMixin, FunctionalTest):
    def get_random_type_id(self):
        hash = random.getrandbits(128)
        return '%032x' % hash

    def test(self):
        type_id = self.get_random_type_id()
        file_id = self.put_file('./tests/images/some.jpeg',
                type_id=type_id)
        self.assertEquals(g.fs.get(file_id).type_id, type_id)
