# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from datetime import datetime
from enum import Enum

from flask_babel import _
from flask_login import UserMixin

from apps import db, login_manager
from apps.authentication.util import hash_pass, verify_pass


class UserRole(Enum):
    ADMIN = _('Admin')
    EDITOR = _('Editor')
    USER = _('User')

class Users(db.Model, UserMixin):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.LargeBinary)
    calendars = db.relationship('Calendar', backref='user', lazy=True)
    events = db.relationship('Event', backref='creator', lazy=True)
    language = db.Column(db.String(2), nullable=False)
    creation = db.Column(db.DateTime(), default=datetime.utcnow())
    update = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())
    email_confirmed = db.Column(db.Boolean(), default=False)
    email_confirmed_on = db.Column(db.DateTime())
    role = db.Column(db.Enum(UserRole), default=UserRole.EDITOR)
    is_admin = db.Column(db.Boolean(), default=False)

    # Status
    @staticmethod
    def is_first_user():
        return Users.query.count() == 0


    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property, value)

    def check_password(self, password):
        return verify_pass(password, self.password)

    def set_password(self, password):
        self.password = hash_pass(password)

    def __repr__(self):
        return str(self.username)


@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    user = Users.query.filter_by(email=email).first()
    return user if user else None
