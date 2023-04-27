from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, DateTimeField, TextAreaField, FieldList, FormField
from wtforms.validators import DataRequired, Length, URL, ValidationError, Email

from apps.home.models import ICal


class CalendarForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=100)])
    description = StringField(_l('Description'), validators=[Length(max=500)])

    submit = SubmitField(_l('Save'), name='cal-form')


class LinkedCalendarForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired(), Length(max=100)])
    color = StringField(_l('Color'), validators=[DataRequired()])
    url = StringField(_l('URL'), description=_l('ICAL Link'), validators=[DataRequired(), URL()])
    cal_id = HiddenField()
    ical_id = HiddenField()
    submit = SubmitField(_l('Save'), name='linked-cal-form')

    def validate_url(self, field):
        url = field.data
        if self.ical_id.data is None or self.ical_id.data == '':
            existing_url = ICal.query.filter_by(url=url, calendar_id=self.cal_id.data).first()
            if existing_url:
                raise ValidationError(_l('This URL already exists.'))

class AttendeeForm(FlaskForm):
    attendee = StringField(_l('Attendee email'), id='eventAttendeeEdit')
class EventForm(FlaskForm):
    title = StringField(_l('Title'), id='eventTitleEdit', validators=[DataRequired()])
    start_time = DateTimeField(_l('Select Start Date'), id='dateStartEdit', render_kw={"placeholder": _l('dd/mm/yyyy')},
                               format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField(_l('Select End Date'), id='dateEndEdit', render_kw={"placeholder": _l('dd/mm/yyyy')},
                             format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    id = HiddenField(id='eventIdEdit')
    location = StringField('Location')
    description = TextAreaField(_l('Description'), id='eventDescriptionEdit')
    attendee = StringField(_l('Attendee email'), id='eventAttendeeEdit')
