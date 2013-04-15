from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def apply_template(self, image_uri, template_uri):
        apply_template_url = '%s?template=%s' % (image_uri, template_uri)
        return self.app.get(apply_template_url, status='*')

    def test_validation(self):
        image_uri = self.put_file('images/some.png')

        corrupted_template_uri = '/template/asds123'
        r = self.apply_template(image_uri, corrupted_template_uri)
        expected_error = 'Template %s does not exist.' % corrupted_template_uri
        
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], expected_error)

        inexistent_template_id = '5087a78f8149954b38d1cbc2'
        inexistent_template_uri = '/template/%s/' % inexistent_template_id
        expected_error = 'Template %s does not exist.' % inexistent_template_uri

        r = self.apply_template(image_uri, inexistent_template_uri)
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], expected_error)

    def test(self):
        r = self.app.post('/template/', {
            'applicable_for': 'image',
            'action[]': ['action=resize&mode=keep&w=400', 'action=grayscale']
        })
        template_uri = r.json['resource_uri']
        image_uri = self.put_file('images/some.png')

        apply_template_url = '%s?template=%s' % (image_uri, template_uri)
        r = self.apply_template(image_uri, template_uri)

        self.run_worker()
        
        self.assertEquals(r.json['status'], 'ok')
        response = self.app.get(r.json['resource_uri'])
        self.assertEquals(response.json['status'], 'ok')

        video_uri = self.put_file('videos/sample.3gp')
        apply_template_url = '%s?template=%s' % (video_uri, template_uri)
        r = self.app.get(apply_template_url, status='*')
        
        self.assertEquals(r.status_code, 400)
        self.assertTrue('not applicable' in r.json['msg'])

    def test_first_action_validation(self):
        watermark_uri = self.put_file('watermarks/watermark.png')
        watermark_action_url = 'action=watermark&watermark=%s&w=5&h=40px&w_pad=10&' \
                               'h_pad=10px&corner=ne' % watermark_uri
        r = self.app.post('/template/', {
            'applicable_for': 'video',
            'action[]': [watermark_action_url]
        })
        template_uri = r.json['resource_uri']
        source_uri = self.put_file('unsupported_videos/29.wmv')

        r = self.apply_template(source_uri, template_uri)
        self.assertEquals(r.json['status'], 'error')
        self.assertEquals(r.json['msg'], 'Sorry, we can\'t handle video stream encoded using wmv3')
