import os
from flask import current_app
import uuid

import requests
from flask import current_app
from werkzeug.utils import secure_filename


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



def sync_events():
    # Get all the calendars
    icals = ICal.query.all()

    # Loop through each calendar
    for ical in icals:
        # Check if it's time to sync this calendar
        if ical.last_synced and (datetime.now() - ical.last_synced).seconds < 300:
            continue

        # Download the ICS data
        response = requests.get(ical.url)

        # Parse the ICS data
        cal = Calendar.from_ical(response.text)

        # Loop through each event in the ICS data
        for event in cal.walk('vevent'):
            # Check if the event already exists in the database
            db_event = Event.query.filter_by(uid=event.get('uid')).first()

            if db_event:
                # If the event already exists, update it
                db_event.summary = event.get('summary')
                db_event.description = event.get('description')
                db_event.start_time = event.get('dtstart').dt
                db_event.end_time = event.get('dtend').dt
                db_event.last_modified = event.get('last-modified').dt
            else:
                # If the event doesn't exist, create it
                db_event = Event(uid=event.get('uid'),
                                  summary=event.get('summary'),
                                  description=event.get('description'),
                                  start_time=event.get('dtstart').dt,
                                  end_time=event.get('dtend').dt,
                                  calendar_id=ical.calendar_id,
                                  last_modified=event.get('last-modified').dt)
                db.session.add(db_event)

        # Update the last_synced field
        ical.last_synced = datetime.now()

    db.session.commit()


