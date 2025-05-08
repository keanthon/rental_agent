from flask import Blueprint, request, jsonify, session
from app.models.user import User
from app import db
from bson.objectid import ObjectId

profile_bp = Blueprint('profile', __name__, url_prefix='/api/profile')

@profile_bp.route('/', methods=['GET'])
def get_profile():
    """Get user profile and preferences"""
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
        "email_review_required": user.email_review_required,
        "rental_preferences": user.rental_preferences
    })

@profile_bp.route('/', methods=['PUT'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    user = User(**user_data)
    
    # Update basic information
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'email_automated' in data:
        user.email_automated = data['email_automated']
    if 'email_review_required' in data:
        user.email_review_required = data['email_review_required']
    
    # Save changes
    user.save()
    
    return jsonify({
        "message": "Profile updated successfully",
        "user": {
            "id": str(user._id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "email_automated": user.email_automated,
            "email_review_required": user.email_review_required
        }
    })

@profile_bp.route('/preferences', methods=['PUT'])
def update_preferences():
    """Update user rental preferences"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    user = User(**user_data)
    
    # Update rental preferences
    if 'rental_preferences' in data:
        user.rental_preferences = data['rental_preferences']
    
    # Save changes
    user.save()
    
    return jsonify({
        "message": "Rental preferences updated successfully",
        "rental_preferences": user.rental_preferences
    })

@profile_bp.route('/password', methods=['PUT'])
def update_password():
    """Update user password"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    user = User(**user_data)
    
    # Check current password
    if not user.check_password(data.get('current_password')):
        return jsonify({"error": "Current password is incorrect"}), 400
    
    # Set new password
    user.set_password(data.get('new_password'))
    
    # Save changes
    user.save()
    
    return jsonify({
        "message": "Password updated successfully"
    })