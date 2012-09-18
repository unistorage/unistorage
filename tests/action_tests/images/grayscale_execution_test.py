from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_id = self.put_file('./images/some.png')

        url = '/%s/' % original_id
        self.check(url, width=43, height=43, mime='image/png')

        grayscale_action_url = url + '?action=grayscale'
        r = self.app.get(grayscale_action_url)
        
        self.run_worker()

        grayscaled_image_url = '/%s/' % r.json['id']
        self.check(grayscaled_image_url, width=43, height=43, mime='image/png')
