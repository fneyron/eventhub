# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from flask_login import login_required, current_user
from flask_babel import lazy_gettext as _l
from wtforms.validators import Email, DataRequired, EqualTo, ValidationError
from apps.authentication.models import Users


# login and registration


class LoginForm(FlaskForm):
    email = StringField(_l('Email'),
                           id='email_login',
                           render_kw={"placeholder": _l('Email')},
                           validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'),
                             id='pwd_login',
                             render_kw={"placeholder": _l('Password')},
                             validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))


class CreateAccountForm(FlaskForm):
    firstname = StringField(_l('First Name'),
                           render_kw={"placeholder": _l('First Name')},
                           id='firsname_create',
                           validators=[DataRequired()])
    lastname = StringField(_l('Last Name'),
                           render_kw={"placeholder": _l('Last Name')},
                           id='lastname_create',
                           validators=[DataRequired()])
    email = StringField(_l('Email'),
                        render_kw={"placeholder": _l('Email')},
                        id='email_create',
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'),
                             render_kw={"placeholder": _l('Password')},
                             id='pwd_create',
                             validators=[DataRequired()])
    #terms = BooleanField(_l('Agree terms'), default=True)


class ProfileForm(FlaskForm):
    firstname = StringField(_l('First Name'),
                            render_kw={"placeholder": _l('First Name')},
                            id='firsname_profile',
                            validators=[DataRequired()])
    lastname = StringField(_l('Last Name'),
                           render_kw={"placeholder": _l('Last Name')},
                           id='lastname_profile',
                           validators=[DataRequired()])
    email = StringField(_l('Email'),
                        id='email_profile',
                        validators=[DataRequired(), Email()])

    scan_notification_email = BooleanField(
        _l('Event Email'),
        description=_l('I want to receive an email when I\'m added to an event.'),
        default=False
    )



    submit = SubmitField(_l('Save All'), name='edit-profile')



class ChangeEmailForm(FlaskForm):
    email = StringField(_l('Email'),
                        id='email_profile',
                        description=_l('Provide your new email address'),
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'),
                             render_kw={"placeholder": _l('Password')},
                             id='pwd_profile',
                             description=_l('Your actual password is required to secure email change.'),
                             validators=[DataRequired()])
    submit = SubmitField(_l('Send Confirmation'), name='change-email')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField(_l('Old Password'),
                                 id='oldpwd_profile', validators=[DataRequired()])
    password = PasswordField(_l('Password'),
                             id='pwd_profile',
                             description=_l('Password should contains at least 6 alphanumerical characters'),
                             validators=[DataRequired(), EqualTo('password_confirm', message='Passwords must match')])
    password_confirm = PasswordField(_l('Confirm Password'),
                                     id='confirmpwd_profile',
                                     validators=[DataRequired()])
    submit = SubmitField(_l('Change password'), name='change-password')

    def validate_old_password(self, field):
        if not current_user.check_password(field.data):
            raise ValidationError(_l('Invalid old password'))


class RecoverPasswordForm(FlaskForm):
    email = StringField(_l('Email'),
                        render_kw={"placeholder": _l('Email')},
                        id='email_recover',
                        validators=[DataRequired(), Email()])


class ResetPasswordForm(FlaskForm):
    email = StringField(_l('Email'),
                        id='email_reset',
                        validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'),
                             id='pwd_reset',
                             validators=[DataRequired(),
                                         EqualTo('password_confirm', message=_l('Passwords must match'))])
    password_confirm = PasswordField(_l('Confirm Password'),
                                     id='confirmpwd_reset',
                                     validators=[DataRequired()])
