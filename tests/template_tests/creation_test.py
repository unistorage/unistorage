from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_create_template(self):
        r = self.app.post('/template/', {
            'action[]': ['action=resize&mode=keep&w=50&h=50', 'action=grayscale'],
            'applicable_for': 'image'
        })
        self.assertEquals(r.json['status'], 'ok')
        self.assertTrue('resource_uri' in r.json)

        r = self.app.get(r.json['resource_uri'])
        information = r.json['information']
        print r.json
        self.assertEquals(information['applicable_for'], 'image')
        self.assertEquals(len(information['action_list']), 2)

    def test_create_template_validation(self):
        r = self.app.post('/template/', {
            'action[]': [],
            'applicable_for': 'image'
        }, status='*')
        self.assertEquals(r.status_code, 400)
        self.assertEquals(r.json['status'], 'error')

        r = self.app.post('/template/', {
            'action[]': ['action=convert&to=webm', 'action=resize&mode=keep&w=100&h=100'],
            'applicable_for': 'video'
        }, status='*')
        self.assertEquals(r.json['status'], 'error')
