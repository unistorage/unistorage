from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_create_template(self):
        r = self.app.post('/create_template', {
            'action[]': ['action=resize&mode=keep&w=50&h=50', 'action=grayscale'],
            'applicable_for': 'image'
        })
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('id' in r.json)

    def test_create_template_validation(self):
        r = self.app.post('/create_template', {
            'action[]': [],
            'applicable_for': 'image'
        }, status='*')
        self.assertEquals(r.status_code, 400)
        self.assertEquals(r.json['status'], 'error')

        r = self.app.post('/create_template', {
            'action[]': ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'],
            'applicable_for': 'video'
        }, status='*')
        self.assertEquals(r.json['status'], 'error')
