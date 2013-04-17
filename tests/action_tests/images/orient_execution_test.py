# coding: utf-8
from tests.utils import StorageFunctionalTest


# Примеры изображений с различной ориентацией:
# https://github.com/recurser/exif-orientation-examples


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        original_uri = self.put_file('images/exif-test.jpg')
        r = self.check(original_uri, width=450, height=600, mime='image/jpeg')
        self.assertEqual(r.json['data']['extra']['orientation'], 8)
       
        resize_action_url = '%s?action=orient' % original_uri
        r = self.app.get(resize_action_url)
        self.assertEquals(r.json['status'], 'ok')

        resized_image_uri = r.json['resource_uri']
        
        self.run_worker()

        r = self.check(resized_image_uri, width=600, height=450, mime='image/jpeg')
        self.assertEqual(r.json['data']['extra']['orientation'], 1)
