# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json

from babel.dates import format_datetime
from flask import Blueprint, session
from datetime import datetime
from babel.dates import format_timedelta

from apps import babel, get_locale

blueprint = Blueprint(
    'home_blueprint',
    __name__,
    url_prefix=''
)


@blueprint.context_processor
def utility_processor():
    def active_language():
        lang_code = session['language'] or get_locale()
        return dict(code=lang_code, name=babel.default_locale.parse(lang_code).get_display_name())

    return dict(active_language=active_language)


@blueprint.app_template_filter('translate')
def translate(value, lang_code=None):
    if lang_code is None:
        lang_code = session.get('language') or get_locale()
    if value:
        if isinstance(value, (str, bytes, bytearray)):
            try:
                json_d = json.loads(value)
            except json.JSONDecodeError as e:
                return value
        else:
            json_d = value

        if lang_code in json_d:
            return json_d[lang_code]
        return next(iter(json_d.values()))
    return value


@blueprint.app_template_filter('json_loads')
def json_loads_filter(value):
    return json.loads(value)


@blueprint.app_template_filter('format_datetime')
def format_datetime_filter(value, format='medium', locale='en'):
    if get_locale():
        locale = get_locale()
    return format_datetime(value, format=format, locale=locale)


@blueprint.app_template_filter('format_timedelta')
def format_timedelta_filter(value, granularity='minute', locale='en'):
    if get_locale():
        locale = get_locale()
    now = datetime.now()
    delta = value - now
    return format_timedelta(delta, locale=locale, granularity=granularity)
