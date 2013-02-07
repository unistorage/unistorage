from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        uri = self.put_file('images/some.png')
        self.check(uri, width=43, height=43, mime='image/png')

        r = self.app.get('%s?action=grayscale' % uri)
        grayscaled_image_url = r.json['resource_uri']
        
        self.run_worker()

        self.check(grayscaled_image_url, width=43, height=43, mime='image/png')
