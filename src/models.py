from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    salt = db.Column(db.String(120))
    hashed_password = db.Column(db.String(80), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), default=False, nullable=False)

    def __init__(self, **kwargs):
        self.email = kwargs.get('email')
        self.salt = os.urandom(16).hex()
        self.set_password(kwargs.get('password'))

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
        print(generate_password_hash(
            f"{password}{self.salt}"
        ))
        self.hashed_password = generate_password_hash(
            f"{password}{self.salt}"
        )

    def check_password(self, password):
        return check_password_hash(
            self.hashed_password,
            f"{password}{self.salt}"
        )

    def __repr__(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            # do not serialize the password, its a security breach
        }

class Admin(db.Model, User):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)


class Professor(db.Model, User):
    __tablename__ = 'professor'
    id= db.Column(db.Integer, primary_key=True)