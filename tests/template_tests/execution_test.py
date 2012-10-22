from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test(self):
        r = self.app.post('/template/', {
            'applicable_for': 'image',
            'action[]': ['action=resize&mode=keep&w=400', 'action=grayscale']
        })
        template_uri = r.json['resource_uri']

        image_uri = self.put_file('images/some.png')
        apply_template_url = '%s?template=%s' % (image_uri, template_uri)
        r = self.app.get(apply_template_url)

        self.assertEquals(r.json['status'], 'ok')

        video_uri = self.put_file('videos/sample.3gp')
        apply_template_url = '%s?template=%s' % (video_uri, template_uri)
        r = self.app.get(apply_template_url, status='*')
        
        self.assertEquals(r.status_code, 400)
        self.assertTrue('not applicable' in r.json['msg'])
