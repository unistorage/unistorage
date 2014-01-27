# coding: utf-8
import random

from app import db, fs
from app.models import User
from tests.utils import StorageFunctionalTest, fixture_path


class FunctionalTest(StorageFunctionalTest):
    def test_broken_jpg(self):
        file_uri = self.put_file('./images/broken/1.jpg')
        response = self.app.get(file_uri).json
        self.assertEqual(response['data']['unistorage_type'], 'unknown')

    def test_jpg_with_location(self):
        file_uri = self.put_file('./images/location.jpeg')
        response = self.app.get(file_uri).json
        self.assertEqual(response['data']['unistorage_type'], 'image')
        self.assertEqual(response['data']['extra']['location'],
                        {'latitude': 56.83, 'longitude': 60.61})
        self.assertEqual(response['data']['extra']['orientation'], 3)


    def test_webm(self):
        file_uri = self.put_file('./videos/video.webm')
        response = self.app.get(file_uri).json
        self.assertEqual(response['data']['unistorage_type'], 'video')

    def test_video_without_video(self):
        file_uri = self.put_file('./videos/broken/no-video.flv')
        response = self.app.get(file_uri).json
        self.assertEqual(response['data']['unistorage_type'], 'audio')
        self.assertEqual(response['data']['extra']['duration'], 210.1)

    def test_pdf(self):
        file_uri = self.put_file('./docs/example.pdf')
        response = self.app.get(file_uri).json
        self.assertEqual(response['data']['extra']['pages'], 10)

    def test_is_aware_of_api_changes(self):
        user = User.get_one(db, {})
        self.assertFalse(user.is_aware_of_api_changes)

        # Заливаем файл
        file_uri = self.put_file('images/some.jpeg')
        # Убеждаемся, что TTL на месте
        self.assertIn('ttl', self.app.get(file_uri))
        
        # Говорим, что пользователь is_aware_of_api_changes
        user.is_aware_of_api_changes = True
        user.save(db)

        # Убеждаемся, что TTL пропал
        self.assertNotIn('ttl', self.app.get(file_uri).json['data'])
