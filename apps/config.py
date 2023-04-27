# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os

from celery.schedules import crontab
from flask_babel import _
from itsdangerous import URLSafeTimedSerializer
from datetime import timedelta


basedir = os.path.abspath(os.path.dirname(__file__))
class Config(object):
    # Set up the App SECRET_KEY
    SECRET_KEY = os.getenv('SECRET_KEY', 'S#perS3crEt_007')

    TS = URLSafeTimedSerializer(SECRET_KEY)
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', 'f495b66803a6512d')

    TIMEZONE = 'Europe/London'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Assets Management
    ASSETS_ROOT = os.getenv('ASSETS_ROOT', '/static/assets')

    UPLOAD_FOLDER = './apps/static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    CKEDITOR_PKG_TYPE = 'advanced'

    LANGUAGES = ['en', 'fr']


    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')

    # EMAIL Server configuration
    MAIL_SERVER = 'mail.gandi.net'
    MAIL_SENDER = ('EventHub', 'contact@dataik.com')
    MAIL_PORT = 465
    MAIL_USE_SSL = True


    # GEOLOCATION OPTIONS
    GEOLOCATION_TIMEOUT = 20
    GEOLOCATION_MAX_AGE = 0


class ProductionConfig(Config):
    DEBUG = False

    # Security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 3600

    # PostgreSQL database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    CELERY_CONFIG = {
        'broker_url': os.environ.get("REDIS_URL"),
        'result_backend': os.environ.get("REDIS_URL"),
    }


class DebugConfig(Config):
    DEBUG = True



    CELERY_CONFIG = {
        'broker_url': 'redis://127.0.0.1:6379',
        'result_backend': 'redis://127.0.0.1:6379',
    }
    CELERYBEAT_SCHEDULE = {
        'sync-events': {
            'task': 'apps.tasks.sync_events',
            'schedule': timedelta(seconds=10),
        },
    }

    # This will create a file in <app> FOLDER
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db.sqlite3')

# Load all possible configurations
config_dict = {
    'Production': ProductionConfig,
    'Debug': DebugConfig
}
