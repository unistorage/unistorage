from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test(self):
        watermark_id = self.put_file('watermarks/watermark.png')
        source_id = self.put_file('videos/gizmo.mp4')

        url = '/%s/' % source_id
        self.check(url, width=560, height=320, mime='video/mp4')
        
        watermark_action_url = url + '?action=watermark&watermark_id=%s' \
                                    '&w=5&h=40px&w_pad=10&h_pad=10px&corner=ne' % watermark_id
        r = self.app.get(watermark_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        watermarked_video_url = '/%s/' % r.json['id']
        self.check(watermarked_video_url, width=560, height=320)
