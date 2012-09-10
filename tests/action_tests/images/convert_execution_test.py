import app
import settings
from tests.utils import FunctionalTest, WorkerMixin, ContextMixin


class FunctionalTest(FunctionalTest, WorkerMixin):
    def test(self):
        original_id = self.put_file('./tests/images/some.jpeg')

        url = '/%s/' % original_id
        self.check(url, width=640, height=480, mime='image/jpeg')
        
        convert_action_url = url + '?action=convert&to=gif'
        r = self.app.get(convert_action_url, headers=self.headers)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_image_url = '/%s/' % r.json['id']
        r = self.check(converted_image_url, width=640, height=480, mime='image/gif')
