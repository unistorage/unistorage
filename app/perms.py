from flask.ext.principal import RoleNeed, Permission


class AccessPermission(Permission):
    def __init__(self, file):
        need = RoleNeed(file.user_id)
        super(AccessPermission, self).__init__(need)
