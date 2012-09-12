from urlparse import urlparse

from flask import url_for
from repoze.who.api import APIFactory, get_api
from repoze.who.interfaces import IChallenger
from repoze.who.plugins.redirector import RedirectorPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.classifiers import default_request_classifier, default_challenge_decider


class StaticUserPlugin(object):
    def authenticate(self, environ, identity):
        try:
            username = identity['login']
            password = identity['password']
        except KeyError:
            return None

        if (username, password) == ('admin', 'admin'):
            return username


class ViewRedirectorPlugin(RedirectorPlugin):
    """The same `RedirectorPlugin`, but takes view name instead of url."""
    def __init__(self, login_url_name, *args, **kwargs):
        super(ViewRedirectorPlugin, self).__init__('', *args, **kwargs)
        self._login_url_name = login_url_name
        
    def challenge(self, *args, **kwargs):
        self.login_url = url_for(self._login_url_name)
        self._login_url_parts = list(urlparse(self.login_url))
        return super(ViewRedirectorPlugin, self).challenge(*args, **kwargs)


def make_repoze_who_api_factory():
    auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
    
    redirector = ViewRedirectorPlugin('admin.login')
    redirector.classifications = {IChallenger: ['browser']}

    static_user_plugin = StaticUserPlugin()

    identifiers = [('auth_tkt', auth_tkt)]
    challengers = [('redirector', redirector)]
    authenticators = [
        ('auth_tkt', auth_tkt),
        ('usermodel', static_user_plugin)
    ]
    mdproviders = []

    return APIFactory(identifiers, authenticators, challengers,
            mdproviders, default_request_classifier,
            default_challenge_decider)
