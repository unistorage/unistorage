from flask.ext.principal import (
    Principal, Identity, AnonymousIdentity, identity_loaded, identity_changed
)

import who
from utils import StorageBlueprint, error


bp = StorageBlueprint('storage', __name__)
principal = Principal(bp, use_sessions=False)

from views import *


who_api_factory = who.make_repoze_who_api_factory()

@bp.errorhandler(401)
def unauthorized_error_handler(e):
    return error({'msg': 'Login failed'}), 401


@bp.errorhandler(403)
def unauthorized_error_handler(e):
    return error({'msg': 'Access denied'}), 403


@principal.identity_loader
def custom_identity_loader():
    who_api = who_api_factory(request.environ)
    repoze_identity = who_api.authenticate()
    if not repoze_identity:
        return

    user = repoze_identity.get('user')
    identity = Identity(user.token)
    identity.user = user
    if user and hasattr(user, 'provides') and user.provides:
        identity.provides.update(user.provides or [])
    return identity


@bp.record
def configure(state):
    @identity_loaded.connect_via(state.app)
    def on_identity_loaded(sender, identity):
        request.user = identity.user
