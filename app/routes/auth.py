from flask import Blueprint, request, jsonify, session
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Check if user already exists
    existing_user = db.users.find_one({"email": data.get('email')})
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400
    
    # Create new user
    new_user = User(
        email=data.get('email'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        phone=data.get('phone')
    )
    
    # Set password
    new_user.set_password(data.get('password'))
    
    # Save to database
    new_user.save()
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": str(new_user._id)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    
    # Find user by email
    user_data = db.users.find_one({"email": data.get('email')})
    if not user_data:
        return jsonify({"error": "Invalid email or password"}), 401
    
    user = User(**user_data)
    
    # Check password
    if not user.check_password(data.get('password')):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Create session
    session['user_id'] = str(user._id)
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": str(user._id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout a user"""
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"})

@auth_bp.route('/user', methods=['GET'])
def get_user():
    """Get current user information"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    user = User(**user_data)
    
    return jsonify({
        "id": str(user._id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone": user.phone,
        "email_automated": user.email_automated,
        "email_review_required": user.email_review_required
    })