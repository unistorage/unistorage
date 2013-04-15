from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        watermark_uri = self.put_file('watermarks/watermark.png')
        source_uri = self.put_file('videos/gizmo.mp4')
        self.check(source_uri,  mime='video/mp4')
        
        watermark_action_url = '%s?action=resize&mode=resize&w=50&h=50' % source_uri
        r = self.app.get(watermark_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_video_url = r.json['resource_uri']
        self.check(watermarked_video_url)
