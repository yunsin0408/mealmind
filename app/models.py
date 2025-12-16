import datetime
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    # Optional list of allergy strings (stored as JSON array)
    allergies = db.Column(db.JSON, nullable=True)

    def __init__(
        self, username, email, password, is_admin=False, is_confirmed=False, confirmed_on=None
    ):
        self.username = username
        self.email = email
        # store password hash in `password` column for compatibility
        self.password = generate_password_hash(password)
        self.created_on = datetime.now()
        self.is_admin = is_admin
        self.is_confirmed = is_confirmed
        self.confirmed_on = confirmed_on
        self.allergies = []

    def __repr__(self):
        return f"<email {self.email}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        # Check against the stored password hash (in `password` column)
        try:
            return check_password_hash(self.password, password)
        except Exception:
            return False

class Admin(User):
    __tablename__ = "admins"
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    # Add any admin-specific fields here

    def __init__(self, username, email, password, is_confirmed=False, confirmed_on=None):
        super().__init__(username, email, password, is_admin=True, is_confirmed=is_confirmed, confirmed_on=confirmed_on)

    def __repr__(self):
        return f"<admin {self.email}>"

class PantryCategory(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    # Self-referential relationship for subcategories
    parent = db.relationship('PantryCategory', remote_side=[id], backref='subcategories')

    def __repr__(self):
        return f"<PantryCategory {self.name}>"

class PantryItem(db.Model):
    __tablename__ = "pantry_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    # Associate pantry items to users so each user has their own pantry
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)  # e.g., "lbs", "cups", "pieces"
    expiration_date = db.Column(db.Date, nullable=True)

    category = db.relationship('PantryCategory', backref='items')
    user = db.relationship('User', backref=db.backref('pantry_items', lazy='dynamic'))

    def __repr__(self):
        return f"<PantryItem {self.name}>"
    
class MealCategory(db.Model):
    __tablename__ = "meal_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<MealCategory {self.name}>"


class SavedRecipe(db.Model):
    __tablename__ = 'saved_recipes'

    id = db.Column(db.Integer, primary_key=True)
    # Use ON DELETE CASCADE so that deleting a user removes their saved recipes
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    meal_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    pantry_ingredients = db.Column(db.JSON, nullable=True)
    missing_ingredients = db.Column(db.JSON, nullable=True)
    instructions = db.Column(db.JSON, nullable=True)
    created_on = db.Column(db.DateTime, default=datetime.now)

    # Configure relationship to cascade deletes from the ORM side as well.
    user = db.relationship('User', backref=db.backref('saved_recipes', cascade='all, delete-orphan', passive_deletes=True))

    def __repr__(self):
        return f"<SavedRecipe {self.meal_name} by user {self.user_id}>"