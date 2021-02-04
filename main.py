from app import app
from flask import render_template, redirect, url_for, flash, current_app, request, session, jsonify, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from flask_principal import RoleNeed, ActionNeed, Permission, \
    identity_loaded, Identity, identity_changed, AnonymousIdentity

from werkzeug.urls import url_parse

from utils.forms import LoginForm, MeetForm, PatientForm, RegistrationForm
from utils.models import Patient, Doctor, Meet, today, get_name, generate_export, import_from_csv
from utils.stats import get_week_stats, get_meets_for_every_doc

import datetime
import os
import pandas as pd
import threading

@identity_loaded.connect
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if hasattr(current_user, 'is_admin'):
        if identity.user.is_admin:
            identity.provides.add(RoleNeed('admin'))


admin = Permission(RoleNeed('admin'))


@app.route('/uploads/<path:filename>')
def export(filename):
    uploads = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'])
    generate_export()
    return send_from_directory(directory=uploads, filename=filename)


@app.route('/import_db', methods=['POST'])
def import_db():
    file = request.files.get('file')
    file.save(app.config['UPLOAD_FOLDER'] + '/import.csv')
    df_types = pd.read_csv('files/types.csv')['types']
    df = pd.read_csv('files/import.csv', encoding='utf-8', dtype=df_types.to_dict())

    df[df['_labels'] == ':Doctor'].to_csv('files/Doctor.csv', sep=',', encoding='utf-8')
    df[df['_labels'] == ':Patient'].to_csv('files/Patient.csv', sep=',', encoding='utf-8')
    df[df['_labels'] == ':Meet'].to_csv('files/Meet.csv', sep=',', encoding='utf-8')

    df[df['_type'] == 'DOCTOR'].to_csv('files/_DOCTOR.csv', sep=',', encoding='utf-8')
    df[df['_type'] == 'PATIENT'].to_csv('files/_PATIENT.csv', sep=',', encoding='utf-8')

    print(import_from_csv())

    return 'True'


@app.route('/admin')
@login_required
@admin.require(http_exception=403)
def admin_page():
    meets = Meet.get_meets_by_date(today)
    meets_in_week = Meet.get_meets_by_cur_week()
    doc, doc_meets = Doctor.get_meet_stats()

    return render_template('admin.html',
                           meets_today=meets,
                           meets_in_week=get_week_stats(meets_in_week),
                           every_doc_meets=get_meets_for_every_doc(doc, doc_meets))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('start_page'))
    form = LoginForm()
    if form.validate_on_submit():
        print('name: {}, password: {}, remember me: {}'.format(form.login.data, form.password.data,
                                                               form.remember_me.data))
        user = Doctor.nodes.get_or_none(login=form.login.data)
        if user is None or not user.check_password(form.password.data):
            flash('Неправильный логин или пароль!!!')
            return redirect(url_for('login'))

        login_user(user, form.remember_me.data)
        identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('start_page')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        doc = Doctor(
            login=form.login.data,
            name=form.name.data,
            surname=form.surname.data,
            middle_name=form.middle_name.data
        )
        doc.set_password(form.password.data)
        doc.save()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()

    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)

    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return redirect(url_for('start_page'))


@app.route('/patients')
@app.route('/')
@login_required
def start_page():
    patients = Patient.nodes.all()
    return render_template('mane_page.html', patients=patients)


@app.route('/patients/update_diagnosis', methods=['POST'])
@login_required
def update_diagnosis():
    data = request.get_json(True)
    diagnosis = data['diagnosis']
    patient_id = int(data['patient_id'])

    patient = Patient.get_patient_by_id(patient_id)
    if patient:
        patient.diagnosis=diagnosis
        patient.save()
        return 'True'

    return 'False'


@app.route('/patients/update_symptoms', methods=['POST'])
@login_required
def update_symptoms():
    data = request.get_json(True)
    print(data)
    symptoms = data['symptoms']
    patient_id = int(data['patient_id'])

    patient = Patient.get_patient_by_id(patient_id)
    if patient:
        patient.symptoms = symptoms
        patient.save()
        return 'True'

    return 'False'


@app.route('/meets')
def get_meets():
    meets = current_user.get_meets_by_date(today)
    form = MeetForm()
    form.patient.choices = [(patient.id, get_name(patient)) for patient in Patient.nodes.all()]
    return render_template('meets.html', date=today, meets=meets, form=form)


@app.route('/meets/get_meets_by_date')
@login_required
def get_meets_by_date():
    date = request.args.get('date')
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    meets = current_user.get_meets_by_date(date.date())

    return jsonify(data=meets)


@app.route('/meets/update_notes', methods=['POST'])
@login_required
def update_notes():
    data = request.get_json(True)
    notes = data['notes']
    meet_id = int(data['meet_id'])

    meet = Meet.get_meet_by_id(meet_id)
    if meet:
        meet.notes = notes
        meet.save()

    return 'success'


@app.route('/meets/create_meet', methods=['POST'])
@login_required
def create_meet():
    form = MeetForm()
    if form.validate_on_submit():
        date = datetime.datetime.strptime(str(form.date.data)+'T'+str(form.time.data), '%Y-%m-%dT%H:%M:%S')
        patient = Patient.get_patient_by_id(form.patient.data)

        new_meet = Meet(meet_datetime=date, notes='')
        new_meet.save()
        new_meet.doctor.connect(Doctor.get_doctor_by_id(current_user.id))
        new_meet.patient.connect(patient)
        return jsonify({
                'meet_id': str(new_meet.id),
                'meet_time': '{}:{}'.format(new_meet.meet_datetime.time().hour, new_meet.meet_datetime.time().minute),
                'patient': '{} {}.{}.'.format(patient.surname, patient.name[0], patient.middle_name[0]),
                'notes': new_meet.notes
            })
    return jsonify(form.errors)


@app.route('/create_patient', methods=['GET', 'POST'])
@login_required
def create_patient():
    form = PatientForm()
    if form.validate_on_submit():
        patient = Patient(
            contract_number=form.contract_code.data,
            name=form.name.data,
            surname=form.surname.data,
            middle_name=form.middle_name.data,
            diagnosis=form.diagnosis.data,
            symptoms=form.symptoms.data,
            is_male=form.is_male.data,
            birth_date=form.birth_date.data
        )
        patient.save()

        return render_template('create_patient.html', title='Register', form=PatientForm())
    return render_template('create_patient.html', title='Register', form=form)


if __name__ == '__main__':
    threading.Timer(3, import_from_csv, args=['http://0.0.0.0:5000/preload']).start()
    app.run(host='0.0.0.0', port='5000')
