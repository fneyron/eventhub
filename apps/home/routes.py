"""
Copyright (c) 2019 - present AppSeed.us
"""

import os

import requests
import shortuuid
from flask import render_template, request, redirect, url_for, send_file, abort, jsonify, flash, Response, current_app
from flask import send_from_directory
from flask_babel import _
from flask_login import current_user
from icalendar import Calendar as ICalendar
from werkzeug.datastructures import MultiDict

from apps import db, celery
from apps import login_manager
from apps.authentication.forms import ProfileForm, ChangePasswordForm, ChangeEmailForm
from apps.authentication.models import Users, UserRole
from apps.authentication.util import generate_confirmation_token
from apps.decorator import authenticated, roles_required
from apps.home import blueprint
from apps.home.forms import PropertyForm, LinkedCalendarForm, EventForm
from apps.home.models import Property, ICal, Event, Attendee
from apps.home.util import get_events, create_ics
from apps.tasks import sync_events, send_email


@blueprint.route('/index', methods=['POST', 'GET'])
@authenticated
def index():
    event = request.args.get('event_id')


    event_form = EventForm()
    return render_template('home/index.html', segment='index', event_form=event_form, event=event)


@blueprint.route('/property', methods=['POST', 'GET'])
def property_list():

    properties = Property.query.all()

    form = PropertyForm(request.form)
    form.street.data = request.form.get('street address-search')
    #print(request.form)
    #print(form.data, form.validate_on_submit())
    if form.validate_on_submit():

        property_uuid = shortuuid.uuid()
        while Property.query.filter_by(uuid=property_uuid).count():
            property_uuid = shortuuid.uuid()

        property = Property(creator_id=current_user.id)
        form.populate_obj(property)
        db.session.add(property)
        db.session.commit()

        return redirect(url_for('home_blueprint.property_list'))

    data = dict(properties=properties)

    return render_template('home/property_list.html', segment='index', data=data, form=form)


@blueprint.route('/property/<uuid>', methods=['GET'])
def property_display(uuid):
    property = Property.query.filter_by(uuid=uuid).first_or_404()
    if not property.active:
        abort(404)
    data = dict(property=property)
    return render_template('home/property_display.html', segment='qrcode', data=data)


@blueprint.route('/property/update', methods=['POST'])
@authenticated
@roles_required(UserRole.ADMIN, UserRole.EDITOR)
def property_update():
    attr = request.form.get('attr')
    value = bool(str(request.form.get('value')).lower() == 'true')
    property_id = request.form.get('property_id')
    property = Property.query.filter_by(id=property_id).first_or_404()

    setattr(property, attr, value)
    db.session.commit()

    # Return a JSON response indicating success
    return jsonify({'status': 'success'})


@blueprint.route('/property/<int:property_id>/edit', methods=['GET', 'POST'])
@authenticated
@roles_required(UserRole.ADMIN, UserRole.EDITOR)
def property_edit(property_id):
    property = Property.query.filter_by(id=property_id).first_or_404()
    data = dict(property=property)

    # forms
    linked_cal_form = LinkedCalendarForm(request.form, obj=property.ical)

    property_form = PropertyForm(request.form, obj=property)
    property_form.street.data = request.form.get('street address-search') if request.form.get('street address-search') else property_form.street.data

    event_form = EventForm()
    print(request.form)
    print(linked_cal_form.data, linked_cal_form.validate_on_submit())
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
                    property.ical.append(ical)
                db.session.commit()
                sync_events.delay(property_id=property.id)
                return redirect(url_for('home_blueprint.property_edit', property_id=property.id))

        if 'property-form' in request.form and property_form.validate_on_submit():
            property_form.populate_obj(property)
            db.session.commit()
            return redirect(url_for('home_blueprint.property_edit', property_id=property.id))

    return render_template('home/property_edit.html', segment='elements', data=data, property_form=property_form,
                           linked_cal_form=linked_cal_form, event_form=event_form)


@blueprint.route('/property/<int:property_id>/delete', methods=['GET', 'POST'])
@authenticated
@roles_required(UserRole.ADMIN, UserRole.EDITOR)
def property_delete(property_id):
    Property.query.filter_by(id=property_id).delete()
    db.session.commit()

    return redirect(url_for('home_blueprint.property_list'))


@blueprint.route('/profile', methods=['GET', 'POST'])
@authenticated
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
                        template='email/default_email_template.html',
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


@blueprint.route('/profile/update', methods=['POST'])
@authenticated
def profile_update():
    # Get the form data from the AJAX request
    form = ProfileForm(request.form)
    current_user.notification_settings.event_notification_email = form.event_notification_email.data
    current_user.notification_settings.reminder_notification_email = form.reminder_notification_email.data

    db.session.commit()

    # Return a JSON response indicating success
    return jsonify({'status': 'success'})


@blueprint.route('/image/<filename>', methods=['GET'])
def image(filename):
    return send_file(os.path.join('./static/uploads/', filename))


@blueprint.route('/static/img/<path:filename>')
def serve_static_file(filename):
    return send_file(os.path.join('.', 'static', 'assets', 'img', filename))


@blueprint.route('/task/<task_name>/start', methods=['GET'])
@authenticated
def task_start(task_name):
    task = celery.signature(task_name)
    res = task.delay()
    return jsonify({'id': res.id})


@blueprint.route('/task/<task_id>/status')
def task_status(task_id):
    task = celery.AsyncResult(task_id)
    return jsonify({'id': task.id, 'status': task.state})


@blueprint.route('/events', methods=['GET'])
def events_json():
    property_id = request.args.get('property_id')
    attendees = request.args.getlist('attendees')
    start = request.args.get('start')
    end = request.args.get('end')

    events = get_events(property_id=property_id, attendees=attendees, start=start, end=end)
    return jsonify(events)


@blueprint.route('/event/<event_id>/update', methods=['POST'])
def event_update(event_id):
    event = Event.query.get(event_id)
    if not event: return jsonify({'success': False, 'error': 'Event not found'})
    data = MultiDict(request.form)
    form = EventForm(data, obj=event)

    if form.validate_on_submit and (
            event.property.creator_id == current_user.get_id() or current_user.role in (UserRole.ADMIN, UserRole.EDITOR)):

        # We delete existing attendees
        db.session.query(Attendee).filter_by(event_id=event.id).delete()
        if not event.ical_id:
            event.start_date = form.start_date.data
            event.end_date = form.end_date.data
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
@authenticated
def linked_calendar_delete(id):
    ical = ICal.query.join(Property).filter(
        ICal.id == id,
        Property.user_id == current_user.id
    ).first_or_404()
    db.session.delete(ical)
    db.session.commit()
    return redirect(url_for('home_blueprint.property_edit', property_id=ical.property_id))


@blueprint.route('/calendar/export', methods=['GET'])
def calendar_export_ics():
    events = get_events(property_id=request.args.get('property_id'),
                                 attendees=request.args.getlist('attendees'))
    return create_ics(events)


@blueprint.route('/icalendar', methods=['GET'])
def icalendar_get_url():
    url = request.args.get('url')
    response = requests.get(url)

    return Response(response.text, content_type='text/calendar')

