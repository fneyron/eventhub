# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import datetime

from flask import render_template, redirect, request, url_for, flash, current_app
from flask_babel import _
from flask_login import (
    current_user,
    login_user,
    login_required,
    logout_user
)

import apps
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm, ResetPasswordForm, RecoverPasswordForm
from apps.authentication.models import Users, UserRole
from apps.authentication.util import verify_pass, confirm_token, generate_confirmation_token, hash_pass
from apps.home.models import Attendee
from apps.tasks import send_email
from apps.authentication.util import send_email_confirmation


@blueprint.route('/')
def route_default():
    if current_user.is_authenticated:
        # Non confirmed email
        if not current_user.email_confirmed: return redirect(url_for("authentication_blueprint.unconfirmed"))

        # User
        # if current_user.role == UserRole.USER:
        #    return redirect(url_for('home_blueprint.profile'))
        return redirect(url_for('home_blueprint.index'))

    return redirect(url_for('authentication_blueprint.login'))


@blueprint.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.email_confirmed:
        return redirect(url_for('authentication_blueprint.route_default'))
    return render_template('accounts/unconfirmed.html', email=current_user.email)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if request.method == 'POST' and login_form.validate_on_submit():
        # read form data
        email = request.form['email']
        password = request.form['password']

        # Locate user
        user = Users.query.filter(Users.email == email).first()

        # Check the password
        if user and verify_pass(password, user.password):
            login_user(user, remember=login_form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        login_form.email.errors.append(_('Wrong email or password'))

    return render_template('accounts/login.html', form=login_form)


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    form = CreateAccountForm(request.form)
    if request.method == 'POST' and form.validate_on_submit():
        email = form.email.data

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            form.email.errors.append(_('Email already registered'))
            return render_template('accounts/register.html',
                                   form=form)

        # else we can create the user
        user = Users(**form.data)
        # set as admin if it's the first user
        if user.is_first_user():
            user.role = UserRole.ADMIN

        # check if there is event associated to this email
        event_attendee = Attendee.query.filter_by(email=user.email).all()
        for attendee in event_attendee:
            attendee.user_id = user.id

        user.language = apps.get_locale()
        db.session.add(user)
        db.session.commit()

        send_email_confirmation(user)

        # Delete user from session
        logout_user()

        return redirect(url_for('authentication_blueprint.route_default'))

    return render_template('accounts/register.html', form=form)


@blueprint.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    try:
        email = confirm_token(token)

    except:
        return render_template('home/page-404.html'), 404
    form = ResetPasswordForm(email=email)

    if form.validate_on_submit():
        user = Users.query.filter_by(email=email).first_or_404()
        user.password = hash_pass(form.password.data)
        db.session.commit()
        flash(_('Password successfully updated'), 'success')
        return redirect(url_for('authentication_blueprint.login'))

    return render_template('accounts/reset-password.html', form=form, token=token)


@blueprint.route('/resend-confirmation')
@login_required
def resend_confirmation():
    send_email_confirmation(current_user)
    return redirect(url_for('authentication_blueprint.unconfirmed'))


@blueprint.route('/email/<token>/confirm')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except Exception as e:
        return render_template('main/page-404.html'), 404
    user = Users.query.filter_by(email=current_user.email if request.args.get('change') else email).first_or_404()
    user.email = email

    if not user.email_confirmed:
        user.email_confirmed = True
        user.email_confirmed_on = datetime.datetime.now()
    db.session.commit()

    return redirect(url_for("authentication_blueprint.route_default"))


@blueprint.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = RecoverPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if not user:
            form.email.errors.append(_('Unknown Email, please check the email address'))
            return render_template('accounts/forgot-password.html', form=form)

        token = generate_confirmation_token(form.email.data)
        recover_url = url_for(
            'authentication_blueprint.reset_with_token',
            token=token,
            _external=True)

        send_email.delay(
            recipients=[user.email],
            subject=_("Password Reset Requested"),
            template='email/authentication_email_template.html',
            text=_(
                "A password reset request has been received. In order to reset your password, please follow this link : %s" % recover_url),
            content='A password reset request has been received. In order to reset your password, please follow this link',
            lang_code=user.language,
            buttons={'url': recover_url, 'text': _('Reset Password')},
        )
        flash(_('A link to reset your password has been sent. Please check you inbox and spam folder'), 'success')
        return redirect(url_for('authentication_blueprint.login'))

    return render_template('accounts/forgot-password.html', form=form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

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
