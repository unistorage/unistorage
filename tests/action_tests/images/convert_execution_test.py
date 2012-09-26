from tests.utils import WorkerMixin, StorageFunctionalTest 


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        original_resource_uri, _ = self.put_file('images/some.jpeg')
        self.check(original_resource_uri, width=640, height=480, mime='image/jpeg')
        
        convert_action_url = '%s?action=convert&to=gif' % original_resource_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_image_url = r.json['resource_uri']
        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')
