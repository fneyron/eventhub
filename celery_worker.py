import os

from dotenv import load_dotenv

from apps import create_app, celery, tasks
from apps.config import config_dict

load_dotenv()

app_config = config_dict['Debug' if os.getenv('FLASK_ENV') == 'development' else 'Production']

app = create_app(app_config)
app.app_context().push()
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    # Sync events from icalendar every 30 seconds
    sender.add_periodic_task(app_config.EVENT_SYNC_FREQUENCY, tasks.sync_events.s())

