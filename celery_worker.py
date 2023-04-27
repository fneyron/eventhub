#!/usr/bin/env python
import os
from apps import create_app, celery
from apps.config import config_dict
from dotenv import load_dotenv

load_dotenv()

app_config = config_dict['Debug' if os.getenv('FLASK_ENV') == 'development' else 'Production']

app = create_app(app_config)
app.app_context().push()

