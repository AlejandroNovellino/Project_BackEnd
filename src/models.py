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

    def serialize(self):
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

class Cathedra(db.Model):
    __tablename__ = "cathedra"
    id = db.Column(db.Integer, primary_key=True)
    credits = db.Column(db.Integer, nullable=False)
    career = db.Column(db.String(40), nullable=False)
    # foreign keys
    coordinator_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    # relations
    coordinator = db.relationship("Professor", backref=db.backref("cathedra", uselist=False))
    courses = db.relationship("Course", backref="cathedra")
    # relations many to many
    professors = db.relationship('Cathedra_asigns', backref='cathedra')

    def serialize(self):
        return {
            "credits": self.credits,
            "career": self.career,
            "coordinator": self.coordinator_id
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

class Professor_student_rel(db.Model):
    __tablename__ = 'professor_student_rel'
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    cathedra_id = db.Column(db.Integer, db.ForeignKey('cathedra.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    #relations many to many
    students = db.relationship('Notes', backref='course')

class Notes(db.Model):
    __tablename_ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id')) 
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))

class Evaluation_plan(db.Model):
    __tablename__ = 'evaluation_plan'
    id = db.Column(db.Integer, primary_key=True)
    # relations
    evaluations = db.relationship('Evaluation', backref='evaluation_plan')

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    percentage = db.Column(db.Integer, nullable=False)
    # foreign keys
    evaluation_plan_id = db.Column(db.Integer, db.ForeignKey('evaluation_plan.id'))
