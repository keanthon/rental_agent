from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin):
    """User model for authentication and profile management"""
    
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.email = kwargs.get('email')
        self.password_hash = kwargs.get('password_hash')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.phone = kwargs.get('phone')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.rental_preferences = kwargs.get('rental_preferences', {})
        self.email_automated = kwargs.get('email_automated', False)
        self.email_review_required = kwargs.get('email_review_required', True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Get user ID for Flask-Login"""
        return str(self._id)
    
    @classmethod
    def find_by_email(cls, email):
        """Find user by email"""
        user_data = db.users.find_one({"email": email})
        if user_data:
            return cls(**user_data)
        return None
    
    @classmethod
    def find_by_id(cls, user_id):
        """Find user by ID"""
        from bson.objectid import ObjectId
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return cls(**user_data)
        return None
    
    def save(self):
        """Save user to database"""
        self.updated_at = datetime.utcnow()
        if not self._id:
            result = db.users.insert_one({
                "email": self.email,
                "password_hash": self.password_hash,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "phone": self.phone,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "rental_preferences": self.rental_preferences,
                "email_automated": self.email_automated,
                "email_review_required": self.email_review_required
            })
            self._id = result.inserted_id
        else:
            from bson.objectid import ObjectId
            db.users.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "email": self.email,
                    "password_hash": self.password_hash,
                    "first_name": self.first_name,
                    "last_name": self.last_name,
                    "phone": self.phone,
                    "updated_at": self.updated_at,
                    "rental_preferences": self.rental_preferences,
                    "email_automated": self.email_automated,
                    "email_review_required": self.email_review_required
                }}
            )
        return self