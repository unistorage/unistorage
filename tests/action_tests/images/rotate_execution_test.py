from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_jpeg(self):
        original_uri = self.put_file('images/some.jpeg')
        self.check(original_uri, width=640, height=480)

        rotate_action_url = '%s?action=rotate&angle=90' % original_uri
        rotated_image = self.app.get(rotate_action_url)
        
        self.run_worker()

        self.check(rotated_image.json['resource_uri'], width=480, height=640)

    def test_gif(self):
        original_uri = self.put_file('images/transparent.gif')
        self.check(original_uri, width=314, height=400)

        rotate_action_url = '%s?action=rotate&angle=270' % original_uri
        rotated_image = self.app.get(rotate_action_url)
        
        self.run_worker()

        self.check(rotated_image.json['resource_uri'], width=400, height=314)
