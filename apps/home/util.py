import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename
from apps.home.models import Event, Attendee


class Upload():
    def __init__(self, file, folder=''):
        self.folder = folder
        self.file = file
        self.errors = []
        self.extension = os.path.splitext(file.filename)[1]
        self.filename = self.file.filename

        if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], self.folder)):
            os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], self.folder))

        if self.file and self.allowed_file():
            exist = True
            while exist:
                random_string = uuid.uuid4().hex[:6]
                new_filename = f"{random_string}{self.extension}"
                new_filename = secure_filename(new_filename)

                if not os.path.isfile(os.path.join(current_app.config['UPLOAD_FOLDER'], self.folder, new_filename)):
                    exist = False
            self.file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], self.folder, new_filename))
            self.filename = new_filename
        else:
            self.errors.append('Invalid filename')

    def allowed_file(self):
        return '.' in self.filename and self.filename.rsplit('.', 1)[1].lower() in current_app.config[
            'ALLOWED_EXTENSIONS']


def get_calendar_events(calendar_id=None, attendees=None, start=None, end=None):
    events_query = Event.query

    if calendar_id:
        events_query = events_query.filter(calendar_id == calendar_id)

    if attendees:
        events_query = (
            events_query
            .join(Attendee)
            .filter(Attendee.email.in_(attendees))
        )

    if start and end:
        events_query = (
            events_query
            .filter(Event.start_time >= start)
            .filter(Event.end_time <= end)
        )

    grouped_events = {}
    for event in events_query.all():
        key = (event.start_time, event.end_time, event.all_day)
        if key not in grouped_events:
            grouped_events[key] = {
                'id': event.id,
                'title': event.new_summary,
                'start': event.start_time.isoformat(),
                'end': event.end_time.isoformat(),
                'description': event.new_description,
                'attendees': [a.email for a in event.attendees],
                'color': event.ical.color,
                'otherColors': [event.ical.color],
                'allDay': event.all_day,
                'disabled': event.ical is not None
            }
        else:
            grouped_events[key]['otherColors'].append(event.ical.color)
            if not grouped_events[key]['title']:
                grouped_events[key]['title'] = event.new_summary
            if not grouped_events[key]['description']:
                grouped_events[key]['description'] = event.new_description

    events = list(grouped_events.values())

    return events
