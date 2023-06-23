import uuid
from datetime import datetime

from babel.dates import format_datetime
from flask import url_for
from flask_babel import _
from flask_babel import gettext
from flask_login import current_user
from sqlalchemy.ext.hybrid import hybrid_property

from apps import db


class Attendee(db.Model):
    __tablename__ = 'Attendee'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'), nullable=False)
    email = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    user = db.relationship('Users', backref='attendee', uselist=False)

    def __init__(self, email, event, user_id=None):
        self.email = email
        self.event_id = event.id
        self.user_id = user_id

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('Event.id'))
    done = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'description': self.description,
            'done': self.done,
        }

class Event(db.Model):
    __tablename__ = 'Event'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String)
    orig_summary = db.Column(db.String)
    orig_description = db.Column(db.String)
    new_summary = db.Column(db.String)
    new_description = db.Column(db.String)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow, default=datetime.utcnow)
    all_day = db.Column(db.Boolean(), default=False)
    property_id = db.Column(db.Integer, db.ForeignKey('Property.id'))
    ical_id = db.Column(db.Integer, db.ForeignKey('ICal.id'))
    attendees = db.relationship('Attendee', backref='event', lazy=True, cascade='all,delete')
    creator_id = db.Column(db.Integer, db.ForeignKey('Users.id'))

    def __repr__(self):
        return (
            f"Event(id={self.id}, uid={self.uid}, orig_summary={self.orig_summary}, "
            f"orig_description={self.orig_description}, new_summary={self.new_summary}, "
            f"new_description={self.new_description}, start_date={self.start_date}, "
            f"end_date={self.end_date}, last_modified={self.last_modified}, "
            f"all_day={self.all_day}, property_id={self.property_id}, "
            f"ical_id={self.ical_id}, creator_id={self.creator_id})"
        )

    def remove_attendee(self, email):
        from apps.authentication.models import Users, Notification
        attendee = Attendee.query.filter_by(email=email, event_id=self.id).first()
        if attendee:
            # Create a notification for the user who was removed from the event
            content = gettext("Deleted the following event <b>{event}</b>".format(
                user=f"{current_user.firstname} {current_user.lastname}",
                event=f"{self.property.name} : {self.new_summary}",
            ), locale=attendee.user.language)
            notification = Notification(
                content=content,
                user_id=attendee.user_id,
                author_id=current_user.id,
            )
            db.session.add(notification)
            db.session.commit()

            db.session.delete(attendee)
            db.session.commit()

    def add_attendee(self, email):
        from apps.authentication.models import Users, Notification
        # Check if the user already exists and if an invitation was already sent for this email
        user = Users.query.filter_by(email=email).first()
        existing_invitation = Attendee.query.filter_by(email=email, user_id=None).first()

        attendee = Attendee(email=email, event=self)
        db.session.add(attendee)

        if not user and not existing_invitation:
            self.send_invitation_email(email)
        elif user:
            self.associate_attendee_with_user(user)
            if user.notification_settings.event_notification_email:
                self.send_invitation_email(email)

        # No notification if we are inviting ourself
        if user and current_user != user:
            content = gettext("Invited you to the following event <a href={event_url}><b>{event}</b></a>".format(
                user=f"{current_user.firstname} {current_user.lastname}",
                event_url=url_for('home_blueprint.index', event_id=self.id),
                event=f"{self.property.name} : {self.new_summary}",
            ), locale=user.language)
            notification = Notification(content=content, user=user, author=current_user)
            db.session.add(notification)
        db.session.commit()

    def send_invitation_email(self, email):
        from apps.tasks import send_email
        lang_code = current_user.language
        send_email.delay(
            recipients=[email],
            lang_code=lang_code,
            subject=_("You've been invited to an event"),
            text=_("You've been invited to an event by %s %s. Please sign-in or register to view the details: %s" % (
                current_user.firstname, current_user.lastname,
                url_for('home_blueprint.index', _external=True))),
            template='email/event_email_template.html',
            content=_(
                'You are receiving this email because %s, invited you to the following event.') %
                    (current_user.firstname),
            event={
                'property': self.property.name,
                'title': self.new_summary,
                'start': format_datetime(self.start_date, format='d MMM YYYY' if self.all_day else 'medium',
                                         locale=lang_code),
                'end': format_datetime(self.end_date, format='d MMM YYYY' if self.all_day else 'medium',
                                       locale=lang_code),
            },
            buttons={'url': url_for('home_blueprint.index', _external=True, event_id=self.id), 'text': _('View Event')},
        )

    def associate_attendee_with_user(self, user):
        attendees = Attendee.query.filter_by(email=user.email).all()
        for attendee in attendees:
            attendee.user_id = user.id
        db.session.commit()


class PropertyUser(db.Model):
    __tablename__ = 'PropertyUsers'

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('Property.id'), primary_key=True)


class Property(db.Model):
    __tablename__ = 'Property'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    # Checkin & Checkout in property timezone
    checkin_time = db.Column(db.Time)
    checkout_time = db.Column(db.Time)
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    street = db.Column(db.String)
    city = db.Column(db.String)
    zip = db.Column(db.String)
    country = db.Column(db.String)
    uuid = db.Column(db.String, default=str(uuid.uuid4()), unique=True)
    creation = db.Column(db.DateTime, default=datetime.utcnow())
    update = db.Column(db.DateTime, onupdate=datetime.utcnow(), default=datetime.utcnow())
    active = db.Column(db.Boolean(), default=True)

    creator_id = db.Column(db.Integer, db.ForeignKey('Users.id'))
    ical = db.relationship('ICal', backref='property', lazy=True, cascade='all,delete')
    events = db.relationship('Event', backref='property', lazy=True, cascade='all,delete')
    property_users = db.relationship('PropertyUser', backref='property', lazy=True)

    @hybrid_property
    def full_address(self):
        return f"{self.street}, {self.city}, {self.zip}, {self.country}"


class ICal(db.Model):
    __tablename__ = 'ICal'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    color = db.Column(db.String)
    creation = db.Column(db.DateTime, default=datetime.utcnow())
    update = db.Column(db.DateTime, onupdate=datetime.utcnow(), default=datetime.utcnow())
    property_id = db.Column(db.Integer, db.ForeignKey('Property.id'), nullable=False)
    url = db.Column(db.String)
    last_synced = db.Column(db.DateTime())
    events = db.relationship('Event', backref='ical', lazy=True, cascade='all,delete')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'property_id': self.property_id,
            'url': self.url,
        }
