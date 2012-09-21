from tests.utils import WorkerMixin, StorageFunctionalTest 


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_id = self.put_file('images/some.jpeg')

        url = '/%s/' % original_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        convert_action_url = url + '?action=convert&to=gif'
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_image_url = '/%s/' % r.json['id']
        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')
