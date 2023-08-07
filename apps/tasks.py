from datetime import datetime, date, time

import requests
from flask import render_template
from flask_babel import force_locale
from flask_mail import Message
from icalendar import Calendar as ICalendar
from sqlalchemy import or_, and_, not_

from apps.config import Config
from apps.home.models import Event, ICal, Property
from . import mail, celery, db


@celery.task(name='apps.tasks.send_email')
def send_email(recipients, **kwargs):
    msg = Message()
    msg.subject = Config.WEBSITE_NAME + ' : ' + kwargs['subject']
    msg.sender = Config.MAIL_SENDER
    msg.recipients = recipients
    with force_locale(kwargs['lang_code']):
        msg.html = render_template(kwargs['template'], data=kwargs)

    if 'text' in kwargs:
        msg.body = kwargs['text']
    print(msg.html)
    mail.send(msg)


@celery.task(name='apps.tasks.sync_events')
def sync_events(property_id=None):
    if property_id is None:
        icals = ICal.query.all()
    else:
        icals = ICal.query.filter_by(property_id=property_id)

    # Loop through each calendar
    for ical in icals:
        # Check if it's time to sync this calendar
        if ical.last_synced and (datetime.now() - ical.last_synced).seconds < 60:
            continue

        # Download the ICS data
        try:
            response = requests.get(ical.url)
            print(f"{ical.name} : {response.status_code}")

            # Parse the ICS data
            cal = ICalendar.from_ical(response.text)
        except Exception as e:
            print(f"Error while processing {ical.url}: {e}")
            continue

        # print(response.text)
        updated_events = set()

        # Loop through each event in the ICS data
        for event in cal.walk('vevent'):
            try:
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
                            Event.start_date == datetime.combine(event.get('dtstart').dt, time.min) if isinstance(
                                event.get('dtstart').dt,
                                date) else event.get('dtstart').dt,
                            Event.end_date == datetime.combine(event.get('dtend').dt, time.min) if isinstance(
                                event.get('dtend').dt,
                                date) else event.get('dtend').dt,
                            Event.ical_id == ical.id,
                            Event.all_day == ('VALUE' in event.get('dtstart').params and event.get('dtstart').params[
                                'VALUE'] == 'DATE')
                        )
                    )
                ).first()
                #print('%s %s %s' % (event.get('summary'), event.get('dtstart').dt, event.get('dtend').dt))
                if db_event:
                    # If the event already exists, update the date start end and full day.
                    db_event.orig_summary = event.get('summary')
                    db_event.orig_description = event.get('description')
                    db_event.start_date = event.get('dtstart').dt
                    db_event.end_date = event.get('dtend').dt
                    if 'VALUE' in event.get('dtstart').params and event.get('dtstart').params['VALUE'] == 'DATE':
                        db_event.all_day = True
                    db.session.commit()
                    print("Update")
                    print(db_event)
                else:
                    # If the event doesn't exist, create it
                    db_event = Event(uid=event.get('uid'),
                                     orig_summary=event.get('summary'),
                                     orig_description=event.get('description'),
                                     new_summary=event.get('summary'),
                                     new_description=event.get('description'),
                                     start_date=event.get('dtstart').dt,
                                     end_date=event.get('dtend').dt,
                                     property_id=ical.property_id,
                                     ical_id=ical.id)
                    if 'VALUE' in event.get('dtstart').params and event.get('dtstart').params['VALUE'] == 'DATE':
                        db_event.all_day = True
                    db.session.add(db_event)
                    db.session.commit()
                    print("Create")
                    print(db_event)
                updated_events.add(db_event)
            except Exception as e:
                print(f"Error occurred during event processing: {e}")
                db.session.rollback()

        try:
            # Delete all other events
            removed_events = Event.query.filter(Event.ical_id == ical.id).filter(
                not_(Event.id.in_([e.id for e in updated_events])))

            for e in removed_events:
                print("Delete")
                print(e)
            removed_events.delete()

            # Update the last_synced field
            ical.last_synced = datetime.now()
            db.session.commit()


        except Exception as e:
            print(f"Error occurred during event deletion: {e}")
            db.session.rollback()
    return {'success': True}
