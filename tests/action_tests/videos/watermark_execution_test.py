from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        watermark_uri = self.put_file('watermarks/watermark.png')
        source_uri = self.put_file('videos/gizmo.mp4')
        self.check(source_uri,  mime='video/mp4')
        
        watermark_action_url = '%s?action=watermark&watermark=%s' \
                               '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % \
                               (source_uri, watermark_uri)
        r = self.app.get(watermark_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_video_url = r.json['resource_uri']
        self.check(watermarked_video_url)
