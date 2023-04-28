# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import hashlib
import os

from flask import url_for, current_app, flash
from flask_babel import _
from itsdangerous import URLSafeTimedSerializer

from apps.config import Config
from apps.tasks import send_email

import binascii

secret_key = Config.SECRET_KEY
secret_pwd = Config.SECURITY_PASSWORD_SALT


def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def generate_confirmation_token(email):
    """ generate token"""

    serializer = URLSafeTimedSerializer(secret_key)

    return serializer.dumps(email, salt=secret_pwd)


def confirm_token(token, expiration=3600):
    """ confirm token """
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(
            token,
            salt=secret_pwd,
            max_age=expiration
        )
    except:
        return False
    return email


def send_email_confirmation(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for('authentication_blueprint.confirm_email', token=token, _external=True)

    send_email.delay(
        recipients=[user.email],
        subject=_("Email confirmation"),
        text=_("To confirm your account, please follow this link : %s") % confirm_url,
        template='email/authentication_email_template.html',
        content='Thank your <b>%s</b> for registering to %s. Please, click the link below to confirm your email address.' %
                (user.firstname, current_app.config['WEBSITE_NAME']),
        lang_code=user.language,
        buttons={'url': confirm_url, 'text': _('Confirm Email')},
    )
    flash(_('A confirmation link has been sent. Please check you inbox and spam folder'), 'success')
