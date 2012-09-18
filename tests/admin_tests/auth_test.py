from flask import url_for

from tests.utils import AdminFunctionalTest


class FunctionalTest(AdminFunctionalTest):
    def setUp(self):
        super(FunctionalTest, self).setUp();
        self.index_url = url_for('admin.index')
        self.login_url = url_for('admin.login')
        self.logout_url = url_for('admin.logout')

    def login(self, login=None, password=None):
        form = self.app.get(self.login_url).form
        form.set('login', login)
        form.set('password', password)
        form.submit()

    def logout(self):
        self.app.get(self.logout_url)
    
    def test(self):
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])

        self.login(login='admin', password='admin')
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 200)

        self.logout()
        r = self.app.get(self.index_url)
        self.assertEquals(r.status_code, 302)
        self.assertTrue(self.login_url in r.headers['Location'])
