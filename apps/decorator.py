from functools import wraps

from flask import redirect, url_for, abort, request, session
from flask_login import current_user



def authenticated(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('authentication_blueprint.login', next=request.url))
        if not current_user.email_confirmed:
            return redirect(url_for('authentication_blueprint.unconfirmed', next=request.url))
        return fn(*args, **kwargs)
    return wrapper

def roles_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.is_anonymous or current_user.role not in roles:
                return redirect(url_for('authentication_blueprint.route_default'))

            return fn(*args, **kwargs)

        return decorated_view

    return wrapper
