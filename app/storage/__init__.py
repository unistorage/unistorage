import who
from utils import StorageBlueprint, error


bp = StorageBlueprint('storage', __name__)
from views import *


who_api_factory = who.make_repoze_who_api_factory()

@bp.errorhandler(401)
def unauthorized_error_handler(e):
    return error({'msg': 'Login failed'}), 401

@bp.before_request
def set_user():
    who_api = who_api_factory(request.environ)
    identity = who_api.authenticate()
    request.user = identity and identity.get('user')
