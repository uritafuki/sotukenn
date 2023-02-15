from flask_login import UserMixin
from . import db

class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def get_id(self):
        return self.id

class Product(db.Model):
    __tablename__ = "production"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))

class Possession(db.Model):
    __tablename__ = "possession"
    primarykey = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    material = db.Column(db.Integer)
    quantity = db.Column(db.Integer)

class Required(db.Model):
    __tablename__ = "required"
    primarykey = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    material = db.Column(db.Integer)
    name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)