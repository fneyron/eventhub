from functools import wraps

from flask import redirect, url_for, abort, request
from flask_login import current_user


def email_confirmed(func):
    """
    Verify user email has been confirmed otherwise redirect to unconfirmed page to send another link
    :param func:
    :return:
    """

    @wraps(func)
    def decorated_function(*args, **kwargs):
        if current_user.email_confirmed is False:
            return redirect(url_for('authentication_blueprint.unconfirmed'))
        return func(*args, **kwargs)

    return decorated_function

#
# def roles_required(*roles):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             if not current_user.is_authenticated:
#                 return redirect(url_for('authentication_blueprint.login', next=request.url))
#
#             if current_user.role not in roles:
#                 return redirect(url_for('authentication_blueprint.route_default'))
#
#             return fn(*args, **kwargs)
#
#         return decorated_view
#
#     return wrapper
