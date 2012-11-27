# -*- coding: utf-8 -*-
from unittest import TestCase
from unicodedata import normalize

from file_utils import secure_filename


class Test(TestCase):
    def n(self, u):
        return normalize('NFKD', u)

    def test(self):
        self.assertEquals(
            self.n(u'йцукенг'),
            self.n(secure_filename(u'йцукенг')))
        self.assertEquals(
            self.n(u'йцукенг_ asd123'),
            self.n(secure_filename(u'йцукенг/ asd123')))
        self.assertEquals(
            self.n(u'_'),
            self.n(secure_filename(u'..')))
        self.assertEquals(
            self.n(u'__some_й_path  asd.jpg..'),
            self.n(secure_filename(u'../some/й/path  asd.jpg..')))
