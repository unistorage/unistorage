import random

from app import fs
from tests.utils import StorageFunctionalTest, fixture_path


class FunctionalTest(StorageFunctionalTest):
    def test_broken_jpg(self):
        file_uri = self.put_file('./images/broken/1.jpg')
        response = self.app.get(file_uri).json
        self.assertEquals(response['data']['unistorage_type'], 'unknown')

    def test_webm(self):
        file_uri = self.put_file('./videos/video.webm')
        response = self.app.get(file_uri).json
        self.assertEquals(response['data']['unistorage_type'], 'video')

    def test_video_without_video(self):
        file_uri = self.put_file('./videos/broken/no-video.flv')
        response = self.app.get(file_uri).json
        self.assertEquals(response['data']['unistorage_type'], 'audio')
        self.assertEquals(response['data']['extra']['duration'], 210.1)
