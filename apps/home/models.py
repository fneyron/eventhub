from datetime import datetime

from flask import url_for
from flask_babel import _
from flask_login import current_user
from babel.dates import format_datetime
from apps import db


class Attendee(db.Model):
    __tablename__ = 'Attendee'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))

    def __init__(self, email, event_id, user_id=None):
        self.email = email
        self.event_id = event_id
        self.user_id = user_id


class Event(db.Model):
    __tablename__ = 'Event'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String)
    orig_summary = db.Column(db.String)
    orig_description = db.Column(db.String)
    new_summary = db.Column(db.String)
    new_description = db.Column(db.String)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow(), default=datetime.utcnow())
    all_day = db.Column(db.Boolean(), default=False)
    calendar_id = db.Column(db.Integer, db.ForeignKey('Calendar.id'))
    ical_id = db.Column(db.Integer, db.ForeignKey('ICal.id'))
    attendees = db.relationship('Attendee', backref='event', lazy=True, cascade='all,delete')
    creator_id = db.Column(db.Integer, db.ForeignKey('Users.id'))

    def add_attendee(self, email):
        from apps.tasks import send_email
        from apps.authentication.models import Users

        # Check if the user already exist
        user = Users.query.filter_by(email=email).first()

        # Check if an invitation was already sent for this email
        send_invitation = not (Attendee.query.filter_by(email=email, user_id=None).first())

        attendee = Attendee(email=email, event_id=self.id)
        db.session.add(attendee)
        db.session.commit()

        if not user:
            # Send invitation if no previous invitation was sent for this email
            if send_invitation:
                lang_code = current_user.language
                send_email.delay(
                    recipients=[email],
                    lang_code=lang_code,
                    subject=_("You've been invited to an event"),
                    text=_("You've been invited to an event by %s %s. Please sign up to view the details: %s" % (
                        current_user.firstname, current_user.lastname,
                        url_for('home_blueprint.index', _external=True))),
                    template='email/event_email_template.html',
                    content=_(
                        'You are receiving this email because %s, invited you to the following event.') %
                            (current_user.firstname),
                    event={
                        'title': self.new_summary,
                        'start': format_datetime(self.start_time, format='medium', locale=lang_code),
                        'end': format_datetime(self.end_time, format='medium', locale=lang_code),
                    },
                    buttons={'url': url_for('home_blueprint.index', _external=True), 'text': _('View Event')},
                )
        else:
            self.associate_attendee_with_user(user)

    def associate_attendee_with_user(self, user):
        attendees = Attendee.query.filter_by(email=user.email).all()
        for attendee in attendees:
            attendee.user_id = user.id
            db.session.add(attendee)
        db.session.commit()


class Calendar(db.Model):
    __tablename__ = 'Calendar'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    street = db.Column(db.String)
    city = db.Column(db.String)
    zip = db.Column(db.String)
    country = db.Column(db.String)
    uuid = db.Column(db.String)
    creation = db.Column(db.DateTime, default=datetime.utcnow())
    update = db.Column(db.DateTime, onupdate=datetime.utcnow(), default=datetime.utcnow())
    active = db.Column(db.Boolean(), default=True)
    ical = db.relationship('ICal', backref='calendar', lazy=True, cascade='all,delete')
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    events = db.relationship('Event', backref='calendar', lazy=True, cascade='all,delete')


class ICal(db.Model):
    __tablename__ = 'ICal'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    color = db.Column(db.String)
    creation = db.Column(db.DateTime, default=datetime.utcnow())
    update = db.Column(db.DateTime, onupdate=datetime.utcnow(), default=datetime.utcnow())
    calendar_id = db.Column(db.Integer, db.ForeignKey('Calendar.id'), nullable=False)
    url = db.Column(db.String)
    last_synced = db.Column(db.DateTime())
    events = db.relationship('Event', backref='ical', lazy=True, cascade='all,delete')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'calendar_id': self.calendar_id,
            'url': self.url,
        }
