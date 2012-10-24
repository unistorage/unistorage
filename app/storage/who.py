from flask import Request, g
from repoze.who.api import APIFactory
from repoze.who.classifiers import default_request_classifier, default_challenge_decider

from app.models import User


class TokenPlugin(object):
    def identify(self, environ):
        request = Request(environ)
        headers = request.headers
        token = headers.get('Token')

        if token:
            return {'token': token}
        else:
            return None

    def remember(self, environ, identity):
        pass

    def forget(self, environ, identity):
        pass
    
    def authenticate(self, environ, identity):
        token = identity['token']
        if User.get_one(g.db, {'token': token}):
            return token
        else:
            return None

    def add_metadata(self, environ, identity):
        token = identity.get('token')
        identity['user'] = User.get_one(g.db, {'token': token})


def make_repoze_who_api_factory():
    token_plugin = TokenPlugin()
    identifiers = [('token_plugin', token_plugin)]
    authenticators = [('token_plugin', token_plugin)]
    mdproviders = [('token_plugin', token_plugin)]
    challengers = []

    return APIFactory(identifiers, authenticators, challengers,
                      mdproviders, default_request_classifier,
                      default_challenge_decider)
