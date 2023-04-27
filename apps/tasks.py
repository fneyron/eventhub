from datetime import datetime, date, time

import requests
from flask_babel import force_locale
from flask_mail import Message
from icalendar import Calendar as ICalendar
from sqlalchemy import or_, and_, not_

from apps.config import Config
from apps.home.models import Event, ICal
from . import mail, celery, db


@celery.task(name='apps.tasks.send_email')
def send_email(recipients, **kwargs):
    msg = Message()
    msg.subject = Config.WEBSITE_NAME + ' : ' + kwargs['subject']
    msg.sender = Config.MAIL_SENDER
    msg.recipients = recipients
    if 'html' in kwargs:
        if 'lang_code' in kwargs:
            with force_locale(kwargs['lang_code']):
                msg.html = kwargs['html']
        else:
            msg.html = kwargs['html']
    if 'text' in kwargs:
        msg.body = kwargs['text']

    mail.send(msg)


@celery.task(name='apps.tasks.sync_events')
def sync_events(calendar_id=None):
    if calendar_id is None:
        icals = ICal.query.all()
    else:
        icals = ICal.query.filter_by(calendar_id=calendar_id)



    # Loop through each calendar
    for ical in icals:
        # Check if it's time to sync this calendar
        #if ical.last_synced and (datetime.now() - ical.last_synced).seconds < 300:
        #    continue

        # Download the ICS data
        response = requests.get(ical.url)

        # Parse the ICS data
        cal = ICalendar.from_ical(response.text)

        updated_events = set()

        # Loop through each event in the ICS data
        for event in cal.walk('vevent'):
            # Check if the event already exists in the database
            db_event = Event.query.filter(
                or_(
                    and_(
                        Event.uid.isnot(None),
                        Event.uid == event.get('uid'),
                        Event.ical_id == ical.id,
                    ),
                    and_(
                        Event.orig_summary == event.get('summary'),
                        Event.start_time == datetime.combine(event.get('dtstart').dt, time.min) if isinstance(
                            event.get('dtstart').dt,
                            date) else event.get('dtstart').dt,
                        Event.end_time == datetime.combine(event.get('dtend').dt, time.min) if isinstance(
                            event.get('dtend').dt,
                            date) else event.get('dtend').dt,
                        Event.ical_id == ical.id,
                        Event.all_day == ('VALUE' in event.get('dtstart').params and event.get('dtstart').params[
                            'VALUE'] == 'DATE')
                    )
                )
            ).first()

            if db_event:
                # If the event already exists, update the date start end and full day.
                db_event.orig_summary = event.get('summary')
                db_event.orig_description = event.get('description')
                db_event.start_time = event.get('dtstart').dt
                db_event.end_time = event.get('dtend').dt
                if 'VALUE' in event.get('dtstart').params and event.get('dtstart').params['VALUE'] == 'DATE':
                    db_event.all_day = True
                db.session.commit()
            else:
                # If the event doesn't exist, create it
                db_event = Event(uid=event.get('uid'),
                                 orig_summary=event.get('summary'),
                                 orig_description=event.get('description'),
                                 new_summary=event.get('summary'),
                                 new_description=event.get('description'),
                                 start_time=event.get('dtstart').dt,
                                 end_time=event.get('dtend').dt,
                                 calendar_id=ical.calendar_id,
                                 ical_id=ical.id)
                if 'VALUE' in event.get('dtstart').params and event.get('dtstart').params['VALUE'] == 'DATE':
                    db_event.all_day = True
                db.session.add(db_event)
                db.session.commit()
            updated_events.add(db_event)
            print(updated_events)

        # Delete all other events
        Event.query.filter(Event.ical_id == ical.id).filter(not_(Event.id.in_([e.id for e in updated_events]))).delete()

        # Update the last_synced field
        ical.last_synced = datetime.now()
        db.session.commit()
    return {'success': True}
