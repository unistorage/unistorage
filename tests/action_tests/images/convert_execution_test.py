from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        uri = self.put_file('images/some.jpeg')
        self.check(uri, width=640, height=480, mime='image/jpeg')
        
        r = self.app.get('%s?action=convert&to=gif' % uri)
        self.assertEquals(r.json['status'], 'ok')
        converted_image_url = r.json['resource_uri']

        self.run_worker()

        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')
