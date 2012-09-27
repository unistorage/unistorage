from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        _, watermark_id = self.put_file('watermarks/watermark.png')
        source_resource_uri, source_id = self.put_file('images/some.jpeg')
        self.check(source_resource_uri, width=640, height=480, mime='image/jpeg')
        
        watermark_action_url = '%s?action=watermark&watermark_id=%s' \
                               '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % \
                               (source_resource_uri, watermark_id)
        r = self.app.get(watermark_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_image_url = r.json['resource_uri']
        r = self.check(watermarked_image_url, width=640, height=480, mime='image/jpeg')
