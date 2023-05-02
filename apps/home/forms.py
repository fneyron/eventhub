from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, DateTimeField, TimeField, TextAreaField, FieldList, FormField
from wtforms.validators import DataRequired, Length, URL, ValidationError, Email

from apps.home.models import ICal


class PropertyForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=100)])
    description = TextAreaField(_l('Description'), validators=[Length(max=500)])
    checkin_time = TimeField(_l('Check-in'), format='%H:%M', validators=[DataRequired()])
    checkout_time = TimeField(_l('Check-out'), format='%H:%M', validators=[DataRequired()])
    street = StringField(_l('Street'), name="street",
                         validators=[DataRequired()])
    zip = StringField(_l('ZIP Code'),
                      validators=[DataRequired()])
    city = StringField(_l('City'),
                       validators=[DataRequired()])
    country = StringField(_l('Country'),
                          validators=[DataRequired()])
    country_code = StringField(_l('Country Code'),
                               validators=[DataRequired()])
    submit = SubmitField(_l('Save'), name='property-form')


class LinkedCalendarForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=100)])
    color = StringField(_l('Color'), validators=[DataRequired()])
    url = StringField(_l('URL'), description=_l('ICAL Link'), validators=[DataRequired(), URL()])
    property_id = HiddenField()
    ical_id = HiddenField()
    submit = SubmitField(_l('Save'), name='linked-cal-form')

    def validate_url(self, field):
        url = field.data
        if self.ical_id.data is None or self.ical_id.data == '':
            existing_url = ICal.query.filter_by(url=url, property_id=self.property_id.data).first()
            if existing_url:
                raise ValidationError(_l('This URL already exists.'))


class EventForm(FlaskForm):
    title = StringField(_l('Title'), id='eventTitleEdit', validators=[DataRequired()])
    start_date = DateTimeField(_l('Select Start Date'), id='dateStartEdit', render_kw={"placeholder": _l('dd/mm/yyyy')},
                               format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_date = DateTimeField(_l('Select End Date'), id='dateEndEdit', render_kw={"placeholder": _l('dd/mm/yyyy')},
                             format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    id = HiddenField(id='eventIdEdit')
    location = StringField('Location')
    description = TextAreaField(_l('Description'), id='eventDescriptionEdit')
    attendee = StringField(_l('Attendee'), id='eventAttendeeEdit',
                           description=_l('Please, add attendee email address of people in charge'))
