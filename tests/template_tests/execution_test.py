from tests.utils import FunctionalTest, ContextMixin


class FunctionalTest(ContextMixin, FunctionalTest):
    def test(self):
        r = self.app.post('/create_template', {
            'applicable_for': 'image',
            'action[]': ['action=resize&mode=keep&w=400', 'action=grayscale']
        }, headers=self.headers)
        template_id = r.json['id']

        image_id = self.put_file('./tests/images/some.png')
        apply_template_url = '/%s/?template=%s' % (image_id, template_id)
        r = self.app.get(apply_template_url, headers=self.headers)

        self.assertEquals(r.json['status'], 'ok')

        video_id = self.put_file('./tests/videos/sample.3gp')
        apply_template_url = '/%s/?template=%s' % (video_id, template_id)
        r = self.app.get(apply_template_url, headers=self.headers, status='*')
        
        self.assertEquals(r.status_code, 400)
        self.assertTrue('not applicable' in r.json['msg'])
