from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_jpeg(self):
        uri = self.put_file('images/some.jpeg')
        self.check(uri, width=640, height=480, mime='image/jpeg')

        r = self.app.get('%s?action=optimize' % uri)
        self.assertEquals(r.json['status'], 'ok')
        converted_image_url = r.json['resource_uri']

        self.run_worker()

        r = self.check(converted_image_url, width=640, height=480, mime='image/jpeg', size_lt=211258)

    def test_png(self):
        uri = self.put_file('images/transparent.png')
        self.check(uri, width=400, height=400, mime='image/png')

        r = self.app.get('%s?action=optimize' % uri)
        self.assertEquals(r.json['status'], 'ok')
        converted_image_url = r.json['resource_uri']

        self.run_worker()

        r = self.check(converted_image_url, width=400, height=400, mime='image/png', size_lt=74402)
