# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_babel import gettext
import os
from importlib import import_module

from apscheduler.schedulers.background import BackgroundScheduler
from celery import Celery
from flask import Flask, request, jsonify
from flask_admin import Admin
from flask_babel import Babel
from flask_ckeditor import CKEditor
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy

app = Flask(__name__)
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
celery = Celery(__name__)
babel = Babel()
ckeditor = CKEditor()
admin = Admin()
scheduler = BackgroundScheduler()


class SQLAlchemy(_BaseSQLAlchemy):
    def apply_pool_defaults(self, app, options):
        super(SQLAlchemy, self).apply_pool_defaults(app, options)
        options["pool_pre_ping"] = app.config['SQLALCHEMY_PRE_PING']

@babel.localeselector
def get_locale():
    user = current_user
    if user.is_authenticated and user.language:
        return user.language

    # Use the Accept-Language header to determine the best language
    return request.accept_languages.best_match(app.config['LANGUAGES'], 'en')

def register_extensions(app):
    db.init_app(app)
    login_manager.init_app(app)
    # Multilingual ext
    babel.init_app(app)

    # Background task ext
    celery.conf.update(app.config["CELERY_CONFIG"])

    # Mail
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    mail.init_app(app)

    # Admin ext
    admin.init_app(app)
    configure_admin(admin, db)

    # CK Editor ext
    ckeditor.init_app(app)



    app.jinja_env.filters['json'] = jsonify


def configure_admin(admin, db):
    from apps.admin import MyModelView, UserAdminView
    from apps.authentication.models import Users, NotificationSettings, Notification
    from apps.home.models import Property, ICal, Event, Attendee
    from flask_admin.contrib.sqla import ModelView

    admin.add_view(UserAdminView(Users, db.session))
    admin.add_view(ModelView(Property, db.session))
    admin.add_view(ModelView(ICal, db.session))
    admin.add_view(ModelView(Event, db.session))
    admin.add_view(ModelView(Attendee, db.session))
    admin.add_view(ModelView(NotificationSettings, db.session))
    admin.add_view(ModelView(Notification, db.session))


def register_blueprints(app):
    for module_name in ('authentication', 'home'):
        module = import_module('apps.{}.routes'.format(module_name))
        app.register_blueprint(module.blueprint)


def configure_database(app):
    @app.before_first_request
    def initialize_database():
        db.create_all()

    @app.teardown_request
    def shutdown_session(exception=None):
        if exception:
            db.session.rollback()
        db.session.remove()


def create_app(config):
    app.config.from_object(config)
    register_extensions(app)
    register_blueprints(app)
    configure_database(app)
    return app
