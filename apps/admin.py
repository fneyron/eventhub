from flask_admin import Admin, AdminIndexView
from flask_admin.form import SecureForm
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user



class UserAdminView(ModelView):
    column_exclude_list = ('password', )
    form_excluded_columns = ('password',)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ['ADMIN']


class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ['ADMIN']

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role.name in ['ADMIN']
