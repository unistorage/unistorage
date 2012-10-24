from tests.utils import StorageFunctionalTest, WorkerMixin


class FunctionalTest(StorageFunctionalTest, WorkerMixin):
    def test_convert_docx_to_html(self):
        original_uri = self.put_file('docs/test.docx')
        r = self.app.get(original_uri)
        self.check(original_uri, mime='application/msword')
        
        convert_action_url = '%s?action=convert&to=html' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = r.json['resource_uri']
        r = self.app.get(converted_doc_url)
        mimetype = r.json['data']['mimetype']
        self.assertTrue('xml' in mimetype or 'html' in mimetype)

    def test_convert_odt_to_pdf(self):
        original_uri = self.put_file('docs/test.odt')

        self.check(original_uri, mime='application/vnd.oasis.opendocument.text')
        convert_action_url = '%s?action=convert&to=pdf' % original_uri
        r = self.app.get(convert_action_url)
        self.assertEquals(r.json['status'], 'ok')

        self.run_worker()

        converted_doc_url = r.json['resource_uri']
        r = self.app.get(converted_doc_url)
        self.check(converted_doc_url, mime='application/pdf')
