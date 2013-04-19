from tests.utils import StorageFunctionalTest


class FunctionalTest(StorageFunctionalTest):
    def test_extract_page_to_png(self):
        original_uri = self.put_file('docs/example.pdf')
        self.check(original_uri, mime='application/pdf')

        extract_page_action_url = '%s?action=extract_page&to=png&page=1' % original_uri
        r = self.app.get(extract_page_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        extracted_page_url = r.json['resource_uri']
        self.check(extracted_page_url, mime='image/png')

    def test_validation(self):
        original_uri = self.put_file('docs/example.pdf')
        extract_page_action_url = '%s?action=extract_page&to=png&page=11' % original_uri
        r = self.app.get(extract_page_action_url, status='*')
        self.assertEquals(r.json['msg'], '`page` must be less that number of pages in the document.')

        extract_page_action_url = '%s?action=extract_page&to=png&page=-1' % original_uri
        r = self.app.get(extract_page_action_url, status='*')
        self.assertEqual(r.status_code, 400)

        extract_page_action_url = '%s?action=extract_page&to=pdf&page=5' % original_uri
        r = self.app.get(extract_page_action_url, status='*')
        self.assertEqual(r.status_code, 400)
