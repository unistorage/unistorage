from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        watermark_uri = self.put_file('watermarks/watermark.png')
        source_uri = self.put_file('images/some.jpeg')
        self.check(source_uri, width=640, height=480, mime='image/jpeg')
        
        watermark_action_url = '%s?action=watermark&watermark=%s' \
                               '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % \
                               (source_uri, watermark_uri)
        r = self.app.get(watermark_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_image_url = r.json['resource_uri']
        r = self.check(watermarked_image_url, width=640, height=480, mime='image/jpeg')

    def test_watermark_overflow(self):
        watermark_uri = self.put_file('watermarks/watermark.png')
        source_uri = self.put_file('images/some.jpeg')
        self.check(source_uri, width=640, height=480, mime='image/jpeg')
        
        watermark_action_url = \
            '%s?action=watermark&watermark=%s' \
            '&w=1000px&h=40px&w_pad=10&h_pad=10px&corner=ne' % \
            (source_uri, watermark_uri)  # w = 1000px
        r = self.app.get(watermark_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'Watermark overflows the source image!')

        watermark_action_url = \
            '%s?action=watermark&watermark=%s' \
            '&w=100px&h=40px&w_pad=100&h_pad=10px&corner=ne' % \
            (source_uri, watermark_uri)  # w_pad = 100
        r = self.app.get(watermark_action_url, status='*')
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'Watermark overflows the source image!')
