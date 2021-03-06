# coding: utf-8
from flask import g

import settings
from app import db
from app.models import User
from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        # Заливаем файл
        file_uri = self.put_file('images/some.jpeg')
        # Берём адрес бинарного содержимого файла
        file_content_url = self.app.get(file_uri).json['data']['url']
        # Смотрим, что он начинается с адреса, указанного в настройках

        self.assertTrue(any([file_content_url.startswith(gridfs_serve_url)
                             for gridfs_serve_url in settings.GRIDFS_SERVE_URLS]))

        # Указываем пользователю список доменов
        user = User.get_one(db, {})
        user.domains = ['http://s.66.ru', 'http://www.ya.ru/']
        user.save(db)

        # Перезапрашиваем адрес
        file_content_url = self.app.get(file_uri).json['data']['url']
        # Удостоверяемся, что адрес начинается с одного из доменов, указанных в user.domains
        self.assertTrue(any([file_content_url.startswith(domain) for domain in user.domains]))
