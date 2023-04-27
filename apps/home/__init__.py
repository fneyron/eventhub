# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import Blueprint, session, current_app
from apps import babel, get_locale
from functools import lru_cache
import json


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