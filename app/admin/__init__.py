from flask import Blueprint

import who

import settings


kwargs = {}
if settings.SERVER_NAME:
    kwargs = {'subdomain': 'admin'}

bp = Blueprint('admin', __name__, **kwargs)
from views import *


who_api_factory = who.make_repoze_who_api_factory()

@bp.errorhandler(401)
def unauthorized_error_handler(error):
    who_api = who_api_factory(request.environ)
    return who_api.challenge()

@bp.before_request
def set_user():
    who_api = who_api_factory(request.environ)
    request.user = who_api.authenticate()
