from flask import Request, g
from repoze.who.api import APIFactory, get_api
from repoze.who.plugins.basicauth import BasicAuthPlugin
from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
from repoze.who.classifiers import default_request_classifier, default_challenge_decider

import settings


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
        if token in settings.TOKENS:
            return token
        else:
            return None

    def add_metadata(self, environ, identity):
        token = identity.get('token')
        users = g.db[settings.MONGO_USERS_COLLECTION_NAME]
        identity['user'] = users.find_one({'token': token}) or \
                users.find_one({'_id': users.insert({'token': token})})


def make_repoze_who_api_factory():
    token_plugin = TokenPlugin()
    identifiers = [('token_plugin', token_plugin)]
    authenticators = [('token_plugin', token_plugin)]
    mdproviders = [('token_plugin', token_plugin)]
    challengers = []

    return APIFactory(
        identifiers,
        authenticators,
        challengers,
        mdproviders,
        default_request_classifier,
        default_challenge_decider
    )
