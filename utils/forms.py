from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DateField, SelectField, \
    IntegerField, TimeField
from wtforms.validators import DataRequired, Optional, ValidationError, Email, EqualTo
from utils.models import Doctor, Patient, Meet
from wtforms.fields.html5 import DateTimeLocalField


class LoginForm(FlaskForm):
    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Sign In')


class MeetForm(FlaskForm):
    time = TimeField('Время встречи', validators=[DataRequired()])
    patient = SelectField('Пациент', validate_choice=False, coerce=int)
    date = DateField()

    submit_meet = SubmitField('Назначить встречу')


class PatientForm(FlaskForm):
    contract_code = StringField('Номер Договора', validators=[DataRequired()])
    name = StringField('Имя пациента', validators=[DataRequired()])
    surname = StringField('Фамилия пациента', validators=[DataRequired()])
    middle_name = StringField('Отчество пациента', validators=[DataRequired()])
    birth_date = DateField('Дата рождение', validators=[DataRequired()])
    is_male = SelectField('Пол', choices=[(1, 'Мужской'), (0, 'Женский')], validators=[DataRequired()], coerce=int)
    symptoms = StringField('Симптомы', validators=[Optional()], default='')
    diagnosis = StringField('Диагноз', validators=[Optional()], default='')

    submit = SubmitField('Добавить пациента')

    def validate_contract_code(self, code):
        patient = Patient.nodes.get_or_none(contract_number=code.data)
        if patient is not None:
            raise ValidationError('Такой пациент уже существует.')


class RegistrationForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])

    name = StringField('Имя доктора', validators=[DataRequired()])
    surname = StringField('Фамилия доктора', validators=[DataRequired()])
    middle_name = StringField('Отчество доктора', validators=[DataRequired()])

    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_login(self, login):
        doctor = Doctor.nodes.get_or_none(login=login.data)
        if doctor is not None:
            raise ValidationError('Логин уже занят.')
