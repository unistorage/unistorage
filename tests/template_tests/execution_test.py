from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        r = self.app.post('/create_template', {
            'applicable_for': 'image',
            'action[]': ['action=resize&mode=keep&w=400', 'action=grayscale']
        })
        template_id = r.json['id']

        image_resource_uri, image_id = self.put_file('images/some.png')
        apply_template_url = '%s?template=%s' % (image_resource_uri, template_id)
        r = self.app.get(apply_template_url)

        self.assertEquals(r.json['status'], 'ok')

        video_resource_uri, video_id = self.put_file('videos/sample.3gp')
        apply_template_url = '%s?template=%s' % (video_resource_uri, template_id)
        r = self.app.get(apply_template_url, status='*')
        
        self.assertEquals(r.status_code, 400)
        self.assertTrue('not applicable' in r.json['msg'])
