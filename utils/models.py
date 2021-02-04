from neomodel import (config, StructuredNode, RelationshipTo, RelationshipFrom,
                      DateTimeProperty, DateProperty, StringProperty, BooleanProperty, One, db, StructuredRel,
                      clear_neo4j_database)

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from app import login_manager

from datetime import timedelta, date, datetime

#config.DATABASE_URL = 'bolt://neo4j:123@localhost:7687'
config.DATABASE_URL = 'bolt://neo4j:test@neo4j:7687'
config.AUTO_INSTALL_LABELS = True

# today = datetime.now().date()
today = date(year=2021, month=1, day=26)
week_start = today - timedelta(days=today.weekday())
week_end = week_start + timedelta(days=6)


def generate_export():

    res, cols = db.cypher_query('''
          CALL apoc.export.csv.all(null, {stream:true})
          YIELD file, nodes, relationships, properties, data
          RETURN file, nodes, relationships, properties, data
     ''')
    with open('files/db.csv', 'w', encoding='utf-8') as f:
        print(res[0][4], file=f)




def import_from_csv(some_args=None):
    clear_neo4j_database(db)
    db.cypher_query('''
                    load csv with headers from 'http://server:5000/uploads/Doctor.csv' as row
                        create (:Doctor{id: toInteger(row._id), name: row.name, surname: row.surname, middle_name: row.middle_name, login: row.login, password: row.password, is_admin: toBoolean(row.is_admin)})
            ''')

    db.cypher_query('''
                    load csv with headers from 'http://server:5000/uploads/Patient.csv' as row
                        create (:Patient{id: toInteger(row._id), birth_date: date(row.birth_date), name: row.name, surname: row.surname, middle_name: row.middle_name, diagnosis: row.diagnosis, symptoms: row.symptoms, is_male: toBoolean(row.is_male), contract_number: row.contract_number})
             ''')

    db.cypher_query('''
                    load csv with headers from 'http://server:5000/uploads/Meet.csv' as row
                        create (:Meet{id: toInteger(row._id), meet_datetime: row.meet_datetime, notes: row.notes})
                 ''')



    db.cypher_query('''
                    load csv with headers from 'http://server:5000/uploads/_DOCTOR.csv' as row
                        match (st) where st.id = toInteger(row._start)
                        match (end) where end.id = toInteger(row._end)
                        create (st)-[:DOCTOR]->(end)
                 ''')
    db.cypher_query('''
                    load csv with headers from 'http://server:5000/uploads/_PATIENT.csv' as row
                        match (st) where st.id = toInteger(row._start)
                        match (end) where end.id = toInteger(row._end)
                        create (st)-[:PATIENT]->(end)
                 ''')

    return True


def get_name(patient):
    return '{} {}.{}.'.format(patient.surname, patient.name[0], patient.middle_name[0])


def date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)+1):
        yield start_date + timedelta(n)


class Patient(StructuredNode):
    name = StringProperty()
    surname = StringProperty()
    middle_name = StringProperty()
    contract_number = StringProperty()
    diagnosis = StringProperty(default='')
    symptoms = StringProperty(default='')
    birth_date = DateProperty()
    is_male = BooleanProperty()

    meet = RelationshipFrom('Meet', 'PATIENT')

    @classmethod
    def get_patient_by_id(cls, doctor_id):
        query = f'''
                            match (n:{cls.__name__}) where ID(n)={doctor_id} return n
                '''
        results, columns = db.cypher_query(query)
        if results:
            return cls.inflate(results[0][0])
        return None


def meet_filter(meet_date):
    def inner_foo(meet):
        return meet.meet_datetime.date() == meet_date
    return inner_foo


class Meet(StructuredNode):
    notes = StringProperty()
    meet_datetime = DateTimeProperty()

    patient = RelationshipTo('Patient', 'PATIENT', cardinality=One)
    doctor = RelationshipTo('Doctor', 'DOCTOR', cardinality=One)

    @classmethod
    def get_meet_by_id(cls, doctor_id):
        query = f'''
                            match (n:{cls.__name__}) where ID(n)={doctor_id} return n
                '''
        results, columns = db.cypher_query(query)
        if results:
            return cls.inflate(results[0][0])
        return None

    @classmethod
    def get_meets_by_date(cls, date):
        meets = cls.nodes.all()
        meets = list(filter(meet_filter(date), meets))

        return len(meets)

    @classmethod
    def get_meets_by_range_date(cls, date_start, date_end):
        meets = cls.nodes.all()
        meet_lens = []
        for date in date_range(date_start, date_end):
            meets_in_date = list(filter(meet_filter(date), meets))
            meet_lens.append(len(meets_in_date))

        return meet_lens

    @classmethod
    def get_meets_by_cur_week(cls):
        return cls.get_meets_by_range_date(week_start, week_end)


class Doctor(StructuredNode, UserMixin):
    name = StringProperty()
    surname = StringProperty()
    middle_name = StringProperty()
    login = StringProperty()
    password = StringProperty()
    is_admin = BooleanProperty()

    meet = RelationshipFrom('Meet', 'DOCTOR')

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    @classmethod
    def get_doctor_by_id(cls, doctor_id):
        query = f'''
                            match (n:{cls.__name__}) where ID(n)={doctor_id} return n
                '''
        results, columns = db.cypher_query(query)
        if results:
            return cls.inflate(results[0][0])
        return None

    def get_meets_by_date(self, date):
        meets = self.meet.all()
        meets = list(filter(meet_filter(date), meets))

        meets_dicts = []
        for meet in meets:
            patient = meet.patient.single()
            time = meet.meet_datetime.time()
            meets_dicts.append({
                'meet_id': str(meet.id),
                'meet_time': '{}:{}'.format(time.hour, time.minute),
                'patient': '{} {}.{}.'.format(patient.surname, patient.name[0], patient.middle_name[0]),
                'notes': meet.notes
            })

        return meets_dicts

    @classmethod
    def get_meet_stats(cls):
        docs = cls.nodes.all()
        x = []
        y = []
        for doc in docs:
            x.append(get_name(doc))
            y.append(len(doc.meet.all()))

        return x, y


@login_manager.user_loader
def load_user(user_id):
    return Doctor.get_doctor_by_id(user_id)
