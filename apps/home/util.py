import datetime
import os
import uuid
from datetime import datetime
from urllib.parse import urlparse

from flask import current_app, make_response, request
from icalendar import Calendar as ICalendar, Event as ICalEvent
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

def get_events(property_id=None, attendees=None, start=None, end=None):
    events_query = Event.query

    if property_id:
        events_query = events_query.filter(property_id == property_id)

    if attendees:
        events_query = (
            events_query
            .join(Attendee)
            .filter(Attendee.email.in_(attendees))
        )

    if start and end:
        events_query = events_query.filter(Event.end_date >= start, Event.start_date <= end)

    events = []
    for event in events_query.all():
        print(event)
        if event.all_day and event.property.checkin_time and event.property.checkout_time:
            event_start = datetime.combine(event.start_date.date(), event.property.checkin_time)
            event_end = datetime.combine(event.end_date.date(), event.property.checkout_time)
            all_day = event.all_day
        else:
            event_start = event.start_date
            event_end = event.end_date
            all_day = event.all_day

        event_dict = {
            'id': event.id,
            'title': event.new_summary,
            'orig_title': event.orig_summary if event.orig_summary else '',
            'start': event_start.isoformat(),
            'end': event_end.isoformat(),
            'checkin': event.property.checkin_time.strftime('%H:%M:%S'),
            'checkout': event.property.checkout_time.strftime('%H:%M:%S'),
            'latitude': event.property.latitude,
            'longitude': event.property.longitude,
            'address': event.property.full_address,
            'description': event.new_description if event.new_description else '',
            'orig_description': event.orig_description if event.orig_description else '',
            'attendees': [a.email for a in event.attendees],
            'color': event.ical.color,
            'allDay': all_day,
            'disabled': event.ical is not None
        }
        events.append(event_dict)

    return events


def create_ics(events):
    # create the ICal export file
    ical = ICalendar()
    ical.add('prodid', 'X-RICAL-TZSOURCE=TZINFO:-//EventHub//Hosting Calendar//EN')
    ical.add('CALSCALE', 'GREGORIAN')
    ical.add('version', '2.0')
    for event in events:
        ical_event = ICalEvent()
        ical_event.add('summary', event['title'])
        start = event['start']
        end = event['end']
        if event['allDay']:
            # event is a full day event
            ical_event.add('dtstart;value=date', datetime.fromisoformat(start).date().strftime('%Y%m%d'))
            ical_event.add('dtend;value=date', datetime.fromisoformat(end).date().strftime('%Y%m%d'))
        else:
            # event is not a full day event
            ical_event.add('dtstart', datetime.fromisoformat(start))
            ical_event.add('dtend', datetime.fromisoformat(end))
        ical_event.add('uid',
                       f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex}@{urlparse(request.host_url).hostname}")
        ical_event.add('description', event.get('description', ''))
        # ical_event.add('location', event.get('location', ''))
        ical.add_component(ical_event)

    ical = ical.to_ical()
    response = make_response(ical)
    response.headers['Content-Disposition'] = 'inline; filename="calendar.ics"'
    response.headers['Content-Type'] = 'text/calendar;charset=utf-8'

    return response
