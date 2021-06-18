import enum
import os

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Role(enum.Enum):
    admin = 1
    coordinator = 2
    professor = 3

#The career should have a specific code i.e. fisica = 1856
class Career(enum.Enum): 
    ingenieria = 1
    medicina = 2
    derecho = 3

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    salt = db.Column(db.String(40), nullable=False)
    hashed_password = db.Column(db.String(240), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    # foreign keys
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    # relations
    professor = db.relationship('Professor', backref=db.backref("user", uselist=False))

    def __init__(self, **kwargs):
        self.email = kwargs.get('email')
        self.salt = os.urandom(16).hex()
        self.set_password(kwargs.get('password'))
        self.role = Role(kwargs.get('role')).name
        if kwargs.get('role') != 1:
            self.professor_id = kwargs.get('professor_id')

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
        return_dict = {
            "id": self.id,
            "email": self.email,
            "role": self.role.name
        }
        if self.professor:
            return_dict["professor"] = self.professor.serialize_when_created()

        return return_dict

class Common_data(db.Model):
    __tablename__ = 'common_data'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(40), nullable=False)
    ci = db.Column(db.String(20), nullable=False, unique=True)
    phone_number = db.Column(db.String(20))
    age = db.Column(db.Integer, nullable=False)
    nationality = db.Column(db.String(40))
    residence = db.Column(db.String(120))
    career = db.Column(db.Enum(Career), nullable=False)

    type = db.Column(db.String(40))

    __mapper_args__ = {
        'polymorphic_identity':'common_data',
        'polymorphic_on':type
    }

    def __repr__(self):
        return f"{self.full_name} {self.ci} {self.phone_number} {self.age} {self.nationality} {self.residence} {self.career}"

    def super_serialize(self):
        return {
            "fullname": self.full_name,
            "ci": self.ci,
            "phone_number": self.phone_number,
            "age": self.age,
            "nationality": self.nationality,
            "residence": self.residence,
            "career": self.career.name
        }

class Professor(Common_data, db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, db.ForeignKey('common_data.id'), primary_key=True)
    # relations
    courses = db.relationship("Course", backref="professor")
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
            career=Career(kwargs["career"]).name
        )

    def __repr__(self):
        return f'Professor {self.id} {self.full_name}'

    def serialize(self):
        return_dict = self.super_serialize()

        if self.courses:
            return_dict["courses"] = list(map(lambda course: course.serialize()["title"], self.courses))

        if self.cathedras:
            return_dict["cathedras"] = list(map(lambda cathedra: cathedra.serialize()["name"], self.cathedras))

        return return_dict

class Cathedra(db.Model):
    __tablename__ = "cathedra"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(4), nullable=False, unique=True)
    credits = db.Column(db.Integer, nullable=False)
    career = db.Column(db.Enum(Career), nullable=False)
    # foreign keys
    coordinator_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    # one to one relation
    coordinator = db.relationship("Professor", backref=db.backref("cathedra", uselist=False))
    # one to many
    courses = db.relationship("Course", backref="cathedra")
    professors = db.relationship('Cathedra_asigns', backref='cathedra')

    def __init__(self, **kwargs):
        super().__init__()
        self.name=kwargs["name"]
        self.code=kwargs["code"]
        self.credits=kwargs["credits"]
        self.career=Career(kwargs["career"]).name

    def __repr__(self):
        return f"{self.name} {self.code} {self.credits} {self.career}"

    def serialize(self):
        return_dict = {
            "id": self.id,
            "name": self.name,
            "credits": self.credits,
            "career": self.career.name
        }

        if self.coordinator:
            return_dict["coordinator"] = list(map(lambda coordinator: coordinator.serialize()["name"], self.coordinator))
        
        if self.courses:
            return_dict["courses"] = list(map(lambda course: course.serialize()["title"], self.courses))

        if self.professors:
            return_dict["professors"] = list(map(lambda professor: professor.serialize()["name"], self.professors))

        return return_dict

class Cathedra_asigns(db.Model):
    __tablename__ = "cathedra_asigns"
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    cathedra_id = db.Column(db.Integer, db.ForeignKey('cathedra.id'))

class Student(Common_data, db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, db.ForeignKey('common_data.id'), primary_key=True)
    # relations 
    grades = db.relationship('Grade', backref='student')

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
            career=Career(kwargs["career"]).name
        )

    def __repr__(self):
        return super().__repr__()

    def serialize(self):
        return_dict = {
            "id": self.id,
            "fullname": self.full_name,
            "ci": self.ci,
            "phone_number": self.phone_number,
            "age": self.age,
            "nationality": self.nationality,
            "residence": self.residence,
            "career": self.career.name
        }

        if self.grades:
            return_dict["grades"] = list(map(lambda grade: grade.serialize()["value"], self.grades))

        return return_dict

class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(40))
    init_date = db.Column(db.DateTime(timezone=False))
    # foreign keys
    cathedra_id = db.Column(db.Integer, db.ForeignKey('cathedra.id'))
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'))
    #relations 
    inscriptions = db.relationship('Inscription', backref='course')
    evaluations = db.relationship('Evaluation', backref='course')

    def serialize(self):
        return_dict = {
            "id": self.id,
            "title": self.title,
            "init_date": self.init_date
        }
        if self.cathedra_id:
            return_dict["cathedra_id"] = self.cathedra_id

        if self.professor_id:
            return_dict["professor_id"] = self.professor_id
        
        if self.inscriptions:
            return_dict["inscriptions"] = list(map(lambda inscription: inscription.serialize(), self.inscriptions))
        
        if self.evaluations:
            return_dict["evaluations"] - list(map(lambda evaluation: evaluation.serialize(), self.evaluations)) 

        return return_dict 

class Inscription(db.Model):
    __tablename_ = 'inscription'
    id = db.Column(db.Integer, primary_key=True)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id')) 
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    # relations
    grades = db.relationship('Grade', backref='inscription')

    def serialize(self):
        return_dict = {
            "id": self.id
        }

        if self.student_id:
            return_dict["student_id"] = self.student_id

        if self.course_id:
            return_dict["course_id"] = self.course_id

        if self.grades:
            return_dict["grades"] = list(map(lambda grade: grade.serialize(), self.grades))

        return return_dict

class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    # foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'))
    inscription_id = db.Column(db.Integer, db.ForeignKey('inscription.id'))

    def serialize(self):
        return_dict = {
            "id": self.id,
            "value": self.value
        }

        if self.student_id:
            return_dict["student_id"] = self.student_id

        if self.evaluation_id:
            return_dict["evaluation_id"] = self.evaluation_id

        if self.inscription_id:
            return_dict["inscription_id"] = self.inscription_id

        return return_dict

class Evaluation(db.Model):
    __tablename__ = 'evaluation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), nullable=False)
    percentage = db.Column(db.Integer, nullable=False)
    # foreign keys
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    # relations
    grades = db.relationship('Grade', backref='evaluation')

    def serialize(self):
        return_dict = {
            "id": self.id,
            "name": self.name,
            "percentage": self.percentage
        }

        if self.course_id: 
            return_dict["course_id"] = self.course_id

        if self.grades:
            return_dict["grades"] = list(map(lambda grade: grade.serialize(), self.grades))

