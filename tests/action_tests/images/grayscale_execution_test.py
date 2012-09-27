from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_resource_uri, _ = self.put_file('images/some.png')
        self.check(original_resource_uri, width=43, height=43, mime='image/png')

        grayscale_action_url = '%s?action=grayscale' % original_resource_uri
        r = self.app.get(grayscale_action_url)
        
        self.run_worker()

        grayscaled_image_url = r.json['resource_uri']
        self.check(grayscaled_image_url, width=43, height=43, mime='image/png')
