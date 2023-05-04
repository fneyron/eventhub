# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
import uuid
from datetime import datetime
from datetime import timedelta
from enum import Enum

from flask_babel import _
from flask_login import UserMixin, current_user
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property

from apps import db, login_manager
from apps.authentication.util import hash_pass, verify_pass


class UserRole(Enum):
    ADMIN = _('Admin')
    EDITOR = _('Editor')
    USER = _('User')


class Users(db.Model, UserMixin):
    __tablename__ = 'Users'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String, default=str(uuid.uuid4()), unique=True)

    firstname = db.Column(db.String)
    lastname = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.LargeBinary)
    language = db.Column(db.String(2), nullable=False, default='fr')
    creation = db.Column(db.DateTime(), default=datetime.utcnow())
    update = db.Column(db.DateTime(), onupdate=datetime.utcnow(), default=datetime.utcnow())
    last_login = db.Column(db.DateTime, default=datetime.utcnow())
    email_confirmed = db.Column(db.Boolean(), default=False)
    email_confirmed_on = db.Column(db.DateTime())
    role = db.Column(db.Enum(UserRole), default=UserRole.USER)

    property_users = db.relationship('PropertyUser', backref='user', lazy=True)

    created_events = db.relationship('Event', backref='creator', lazy=True)
    created_properties = db.relationship('Property', backref='creator', lazy=True)

    created_notifications = db.relationship('Notification', backref='author', lazy=True, foreign_keys="[Notification.author_id]")
    notifications = db.relationship('Notification', backref='user', lazy=True, foreign_keys="[Notification.user_id]")

    notification_settings_id = db.Column(db.Integer, db.ForeignKey('NotificationSettings.id'))
    notification_settings = db.relationship('NotificationSettings', backref='user', uselist=False)

    def add_notification(self, content):
        notification = Notification(user_id=self.id, content=content, author_id=current_user.get_id())
        db.session.add(notification)
        db.session.commit()

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
        return str(self.email)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.name,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def last_sync(self):
        from apps.home.models import ICal
        return ICal.query.filter()

class NotificationSettings(db.Model):
    __tablename__ = 'NotificationSettings'

    id = db.Column(db.Integer, primary_key=True)
    event_notification_email = db.Column(db.Boolean(), default=False)
    reminder_notification_email = db.Column(db.Boolean(), default=False)
    reminder_time_minutes = db.Column(db.Integer, default=1440)  # Default to 1 day (1440 minutes)

    @hybrid_property
    def reminder_time(self):
        return timedelta(minutes=self.reminder_time_minutes)

    @reminder_time.setter
    def reminder_time(self, value):
        self.reminder_time_minutes = value.total_seconds() // 60



class Notification(db.Model):
    __tablename__ = 'Notification'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    url = db.Column(db.String)
    author_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    read_status = db.Column(db.Boolean(), default=False)


# Charge l'utilisateur

@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    user = Users.query.filter_by(email=email).first()
    return user if user else None
