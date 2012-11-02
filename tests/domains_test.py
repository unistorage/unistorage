# -*- coding: utf-8 -*-
from flask import g

import settings
from app.models import User
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        # Заливаем файл
        file_uri = self.put_file('images/some.jpeg')
        # Берём адрес бинарного содержимого файла
        file_content_uri = self.app.get(file_uri).json['data']['uri']
        # Смотрим, что он начинается с адреса, указанного в настройках
        self.assertTrue(file_content_uri.startswith(settings.GRIDFS_SERVE_URL))

        # Указываем пользователю список доменов
        user = User.get_one(g.db, {})
        user.domains = ['http://s.66.ru', 'http://www.ya.ru/']
        user.save(g.db)

        # Перезапрашиваем адрес
        file_content_uri = self.app.get(file_uri).json['data']['uri']
        # Удостоверяемся, что адрес начинается с одного из доменов, указанных в user.domains
        self.assertTrue(any([file_content_uri.startswith(domain) for domain in user.domains]))
