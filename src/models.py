import enum
import os

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role(enum.Enum):
    admin = 1
    coordinator = 2
    professor = 3

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    salt = db.Column(db.String(40), nullable=False)
    hashed_password = db.Column(db.String(240), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)

    def __init__(self, **kwargs):
        self.email = kwargs.get('email')
        self.salt = os.urandom(16).hex()
        self.set_password(kwargs.get('password'))
        self.role = Role(kwargs.get('role')).name

    @classmethod
    def create(cls, **kwargs):
        user = cls(**kwargs)
        db.session.add(user)
        try: 
            db.session.commit()
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return False
        return user

    def set_password(self, password):
        self.hashed_password = generate_password_hash(
            f"{password}{self.salt}"
        )

    def check_password(self, password):
        return check_password_hash(
            self.hashed_password,
            f"{password}{self.salt}"
        )

    def __repr__(self):
        return '<User %r>' % self.email

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role.name
            # do not serialize the password, its a security breach
        }

class Common_data(db.Model):
    __tablename__ = 'common_data'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(40), nullable=False)
    ci = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20))
    age = db.Column(db.Integer, nullable=False)
    nationality = db.Column(db.String(40))
    residence = db.Column(db.String(120))
    career = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(40))

    __mapper_args__ = {
        'polymorphic_identity':'common_data',
        'polymorphic_on':type
    }

    def super_serialize(self):
        return {
            "fullname": self.full_name,
            "ci": self.ci,
            "phone_number": self.phone_number,
            "age": self.age,
            "nationality": self.nationality,
            "residence": self.residence,
            "career": self.career
        }

class Professor(Common_data, db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, db.ForeignKey('common_data.id'), primary_key=True)
    # relations
    courses = db.relationship("Course", backref="professor")
    # relations many to many
    students = db.relationship('Professor_student_rel', backref='professor')
    cathedras = db.relationship('Cathedra_asigns', backref='professor')

    __mapper_args__ = {
        'polymorphic_identity':'professor'
    }

    def __init__(self, **kwargs):
        super().__init__(
            full_name=kwargs["full_name"],
            ci=kwargs["ci"],
            phone_number=kwargs["phone_number"],
            age=kwargs["age"],
            nationality=kwargs["nationality"],
            residence=kwargs["residence"],
            career=kwargs["career"]
        )

    def __repr__(self):
        return f'Professor {self.id} {self.full_name}'

    def serialize_when_created(self):
        dict_to_return = self.super_serialize()
        dict_to_return.update(
            {"cathedras":  list(map(lambda cathedra: cathedra.cathedra.serialize_when_created()["name"], self.cathedras))}
        )
        return dict_to_return

    def serialize(self):
        return {
            "id": self.id,
            "fullname": self.full_name,
            "ci": self.ci,
            "phone_number": self.phone_number,
            "age": self.age,
            "nationality": self.nationality,
            "residence": self.residence,
            "career": self.career,
            "courses": list(map(lambda course: course.serialize()["title"], self.courses)),
            "students": list(map(lambda student: student.serialize()["name"], self.students)),
            "cathedras": list(map(lambda cathedra: cathedra.serialize()["name"], self.cathedras))
        }

class Cathedra(db.Model):
    __tablename__ = "cathedra"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False, unique=True)
    code = db.Column(db.String(4), nullable=False, unique=True)
    credits = db.Column(db.Integer, nullable=False)
    career = db.Column(db.String(40), nullable=False)
    # foreign keys
    coordinator_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    # relations
    coordinator = db.relationship("Professor", backref=db.backref("cathedra", uselist=False))
    courses = db.relationship("Course", backref="cathedra")
    # relations many to many
    professors = db.relationship('Cathedra_asigns', backref='cathedra')

    def serialize_when_created(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "credits": self.credits,
            "career": self.career
        }

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "credits": self.credits,
            "career": self.career,
            "coordinator": list(map(lambda coordinator: coordinator.serialize()["name"], self.coordinator)),
            "courses": list(map(lambda course: course.serialize()["title"], self.courses)),
            "professors": list(map(lambda professor: professor.serialize()["name"], self.professors))
        }

class Cathedra_asigns(db.Model):
    __tablename__ = "cathedra_asigns"
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    cathedra_id = db.Column(db.Integer, db.ForeignKey('cathedra.id'))

class Student(Common_data, db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, db.ForeignKey('common_data.id'), primary_key=True)
    # relations many to many
    notes = db.relationship('Notes', backref='student')

    __mapper_args__ = {
        'polymorphic_identity':'student'
    }

    def __init__(self, **kwargs):
        super().__init__(
            full_name=kwargs["full_name"],
            ci=kwargs["ci"],
            phone_number=kwargs["phone_number"],
            age=kwargs["age"],
            nationality=kwargs["nationality"],
            residence=kwargs["residence"],
            career=kwargs["career"]
        )

    def serialize(self):
        return {
            "id": self.id,
            "fullname": self.full_name,
            "ci": self.ci,
            "phone_number": self.phone_number,
            "age": self.age,
            "nationality": self.nationality,
            "residence": self.residence,
            "career": self.career,
            "notes": list(map(lambda note: note.serialize()["note"], self.notes))
        }

class Professor_student_rel(db.Model):
    __tablename__ = 'professor_student_rel'
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    init_date = db.Column(db.DateTime(timezone=False))
    # foreign keys
    cathedra_id = db.Column(db.Integer, db.ForeignKey('cathedra.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    #relations many to many
    students = db.relationship('Notes', backref='course')

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "init_date": self.init_date,
            "students": map(list(lambda student: student.serialize()["name"], self.students))
        }

class Notes(db.Model):
    __tablename_ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Integer)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id')) 
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

    def serialize(self):
        return {
            "note": self.note
        }

class Evaluation_plan(db.Model):
    __tablename__ = 'evaluation_plan'
    id = db.Column(db.Integer, primary_key=True)
    # relations
    evaluations = db.relationship('Evaluation', backref='evaluation_plan')

    def serialize(self):
        return {
            "evaluations": list(map(lambda evaluation: evaluation.serialize(), self.evaluations))
        }

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    percentage = db.Column(db.Integer, nullable=False)
    # foreign keys
    evaluation_plan_id = db.Column(db.Integer, db.ForeignKey('evaluation_plan.id'))

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "percentage": self.percentage
        }
