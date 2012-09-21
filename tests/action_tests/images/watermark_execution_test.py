from tests.utils import FunctionalTest, WorkerMixin, ContextMixin


class FunctionalTest(FunctionalTest, WorkerMixin):
    def test(self):
        watermark_id = self.put_file('./tests/watermarks/watermark.png')
        source_id = self.put_file('./tests/images/some.jpeg')

        url = '/%s/' % source_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        watermark_action_url = url + '?action=watermark&watermark_id=%s' \
                                    '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % watermark_id
        r = self.app.get(watermark_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_image_url = '/%s/' % r.json['id']
        r = self.check(watermarked_image_url, width=640, height=480, mime='image/jpeg')
