# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import hashlib
from flask_babel import _, lazy_gettext
from itsdangerous import URLSafeTimedSerializer
from apps.config import Config
from apps.tasks import send_email
from flask import render_template, redirect, request, url_for
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

def send_email_change_confirmation(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('authentication_blueprint.confirm_email_change', token=token, _external=True)
    subject = _("QRly : New Email requested")
    recipients = [email]
    text_body = _("To confirm your new email address, please follow this link : %s") % confirm_url

    send_email.delay(recipients, subject=subject, text=text_body)

def send_email_confirmation(email):
    token = generate_confirmation_token(email)
    confirm_url = url_for('authentication_blueprint.confirm_email', token=token, _external=True)
    subject = _("Email confirmation")
    recipients = [email]
    text_body = _("To confirm your account, please follow this link : %s") % confirm_url

    send_email.delay(recipients, subject=subject, text=text_body)