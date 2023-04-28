# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests
import shortuuid
from flask import render_template, request, redirect, url_for, send_file, abort, jsonify, flash, Response, \
    make_response, current_app
from flask_babel import _
from flask_login import login_required, current_user
from icalendar import Calendar as ICalendar, Event as ICalEvent
from werkzeug.datastructures import MultiDict

from apps import db, celery
from apps import login_manager
from apps.authentication.forms import ProfileForm, ChangePasswordForm, ChangeEmailForm
from apps.authentication.models import Users, UserRole
from apps.authentication.util import send_email_confirmation, generate_confirmation_token
from apps.decorator import roles_required
from apps.home import blueprint
from apps.home.forms import CalendarForm, LinkedCalendarForm, EventForm
from apps.home.models import Calendar, ICal, Event, Attendee
from apps.home.util import get_calendar_events, create_ics
from apps.tasks import sync_events, send_email


@blueprint.route('/index', methods=['POST', 'GET'])
# @roles_required(UserRole.ADMIN, UserRole.EDITOR)
@login_required
def index():
    event_form = EventForm()
    return render_template('home/index.html', segment='index', event_form=event_form)


@blueprint.route('/calendar', methods=['POST', 'GET'])
@roles_required(UserRole.ADMIN, UserRole.EDITOR)
@login_required
def calendar_list():
    form = CalendarForm(request.form)
    calendars = Calendar.query.all()

    if form.validate_on_submit():

        # Manage QRcode uuid
        calendar_uuid = shortuuid.uuid()
        while Calendar.query.filter_by(uuid=calendar_uuid).count():
            calendar_uuid = shortuuid.uuid()

        # Add qrcode and the language
        calendar = Calendar(uuid=calendar_uuid, name=form.name.data, description=form.description.data,
                            user_id=current_user.get_id())

        db.session.add(calendar)

        db.session.commit()

        return redirect(url_for('home_blueprint.index'))

    data = dict(calendars=calendars)

    return render_template('home/calendar_list.html', segment='index', data=data, form=form)


@blueprint.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm(request.form, obj=current_user)
    profile_form.email.data = current_user.email
    pwd_form = ChangePasswordForm(request.form)
    email_form = ChangeEmailForm(obj=current_user)

    if request.method == 'POST':
        if 'change-email' in request.form and email_form.validate_on_submit():
            if current_user.check_password(email_form.password.data):
                if Users.query.filter_by(email=email_form.email.data).first():
                    email_form.email.errors.append(_('This email address is already registered.'))
                else:
                    token = generate_confirmation_token(email_form.email.data)
                    confirm_url = url_for('authentication_blueprint.confirm_email', token=token, change=True,
                                          _external=True)

                    send_email.delay(
                        recipients=[email_form.email.data],
                        subject=_("Email change"),
                        text=_("To confirm your new email address, please follow this link : %s") % confirm_url,
                        template='email/authentication_email_template.html',
                        content=_('To confirm your new email address, please click the link below.'),
                        lang_code=current_user.language,
                        buttons={'url': confirm_url, 'text': _('Confirm Change')},
                    )
                    flash(_('A confirmation link has been sent to your email. Please check you inbox and spam folder'),
                          'success')
            else:
                email_form.password.errors.append(_('Wrong password provided.'))
        if 'change-password' in request.form and pwd_form.validate_on_submit():
            if current_user.check_password(pwd_form.old_password.data):
                current_user.set_password(pwd_form.password.data)
                flash(_('Password changed'), 'success')

        if 'edit-profile' in request.form and profile_form.validate_on_submit():
            profile_form.populate_obj(current_user)
            flash(_('New profile successfully saved'), 'success')
        db.session.commit()

    return render_template('home/profile.html', segment='profile',
                           profile_form=profile_form, email_form=email_form, pwd_form=pwd_form)


@blueprint.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    # Get the form data from the AJAX request
    form = ProfileForm(request.form)
    current_user.scan_notification_email = form.scan_notification_email.data

    db.session.commit()

    # Return a JSON response indicating success
    return jsonify({'status': 'success'})


@blueprint.route('/image/<filename>', methods=['GET'])
def image(filename):
    return send_file(os.path.join('./static/uploads/', filename))


@blueprint.route('/calendar/update', methods=['POST'])
@login_required
def calendar_update():
    attr = request.form.get('attr')
    value = bool(str(request.form.get('value')).lower() == 'true')
    calendar_id = request.form.get('calendar_id')
    calendar = Calendar.query.filter_by(id=calendar_id).first_or_404()

    if calendar.user == current_user:
        setattr(calendar, attr, value)
        db.session.commit()

    # Return a JSON response indicating success
    return jsonify({'status': 'success'})


@blueprint.route('/calendar/<int:calendar_id>/edit', methods=['GET', 'POST'])
@login_required
def calendar_edit(calendar_id):
    calendar = Calendar.query.filter_by(id=calendar_id).first_or_404()
    data = dict(calendar=calendar)

    # forms
    linked_cal_form = LinkedCalendarForm(request.form, obj=calendar.ical)
    cal_form = CalendarForm(request.form, obj=calendar)
    event_form = EventForm()

    if request.method == 'POST':
        if 'linked-cal-form' in request.form and linked_cal_form.validate_on_submit():
            is_valid = True
            try:
                response = requests.get(linked_cal_form.url.data)
                ICalendar.from_ical(response.text)
            except Exception as e:
                is_valid = False
                linked_cal_form.url.errors.append(_('Ical format not recognized'))

            if is_valid:
                if linked_cal_form.ical_id.data:
                    # Editing an existing ICal object
                    ical = ICal.query.filter_by(id=linked_cal_form.ical_id.data).first_or_404()
                    linked_cal_form.populate_obj(ical)
                else:
                    ical = ICal()
                    linked_cal_form.populate_obj(ical)
                    calendar.ical.append(ical)
                db.session.commit()
                sync_events.delay(calendar_id=calendar.id)
                return redirect(url_for('home_blueprint.calendar_edit', calendar_id=calendar.id))

        if 'cal-form' in request.form and cal_form.validate_on_submit():
            cal_form.populate_obj(calendar)
            db.session.commit()

    return render_template('home/calendar_edit.html', segment='elements', data=data, cal_form=cal_form,
                           linked_cal_form=linked_cal_form, event_form=event_form)


@blueprint.route('/task/<task_name>/start', methods=['GET'])
@login_required
def task_start(task_name):
    task = celery.signature(task_name)
    res = task.delay()
    return jsonify({'id': res.id})


@blueprint.route('/task/<task_id>/status')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({'id': task.id, 'status': task.state})


@blueprint.route('/calendar/<uuid>', methods=['GET'])
def calendar_display(uuid):
    calendar = Calendar.query.filter_by(uuid=uuid).first_or_404()
    if not calendar.active:
        abort(404)
    data = dict(calendar=calendar)
    return render_template('home/calendar_display.html', segment='qrcode', data=data)


@blueprint.route('/calendar/events', methods=['GET'])
def calendar_events_json():
    calendar_id = request.args.get('calendar_id')
    attendees = request.args.getlist('attendees')
    start = request.args.get('start')
    end = request.args.get('end')

    events = get_calendar_events(calendar_id=calendar_id, attendees=attendees, start=start, end=end)
    return jsonify(events)


@blueprint.route('/event/<event_id>/update', methods=['POST'])
def event_update(event_id):
    event = Event.query.get(event_id)
    if not event: return jsonify({'success': False, 'error': 'Event not found'})
    data = MultiDict(request.form)
    form = EventForm(data, obj=event)

    if form.validate_on_submit and (
            event.calendar.user == current_user or current_user.role in (UserRole.ADMIN, UserRole.EDITOR)):

        # We delete existing attendees
        db.session.query(Attendee).filter_by(event_id=event.id).delete()
        if not event.ical_id:
            event.start_time = form.start_time.data
            event.end_time = form.end_time.data
        event.new_summary = form.title.data
        event.new_description = form.description.data

        from wtforms.validators import Email
        from wtforms import ValidationError

        for attendee in data.getlist('attendee[]'):
            form.attendee.data = attendee
            validator = Email()
            try:
                validator(None, form.attendee)
                event.add_attendee(attendee)
                user = Users.query.filter_by(email=attendee).first()
                if user:
                    event.associate_attendee_with_user(user)
            except ValidationError:
                form.attendee.errors.append(_('Invalid email address'))

        db.session.commit()

    return jsonify({'success': not (form.errors), 'errors': form.errors})


@blueprint.route('/user/<value>/json', methods=['GET'])
def get_user_json(value):
    users = Users.query.filter(Users.email.like(value + '%')).all()
    attendee = Attendee.query.filter(Attendee.email.like(value + '%')).all()
    return jsonify(list(set([user.email for user in users + attendee])))


@blueprint.route('/linkedcal/<int:id>/delete', methods=['GET'])
@login_required
def linked_calendar_delete(id):
    ical = ICal.query.join(Calendar).filter(
        ICal.id == id,
        Calendar.user_id == current_user.id
    ).first_or_404()
    db.session.delete(ical)
    db.session.commit()
    return redirect(url_for('home_blueprint.calendar_edit', calendar_id=ical.calendar_id))


@blueprint.route('/calendar/export', methods=['GET'])
def calendar_export_ics():
    events = get_calendar_events(calendar_id=request.args.get('calendar_id'),
                                 attendees=request.args.getlist('attendees'))

    return create_ics(events)


@blueprint.route('/icalendar', methods=['GET'])
def icalendar_get_url():
    url = request.args.get('url')
    response = requests.get(url)

    return Response(response.text, content_type='text/calendar')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
