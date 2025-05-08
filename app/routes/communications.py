from flask import Blueprint, request, jsonify, session
from app.services.email_service import EmailService
from app.models.listing import Listing
from app.models.user import User
from app.models.communication import Communication
from app import db
from bson.objectid import ObjectId
from datetime import datetime

communications_bp = Blueprint('communications', __name__, url_prefix='/api/communications')

email_service = EmailService()

@communications_bp.route('/draft/<listing_id>', methods=['POST'])
def create_draft(listing_id):
    """Create a draft email for a listing"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get user
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    user = User(**user_data)
    
    # Get listing
    listing_data = db.listings.find_one({"_id": ObjectId(listing_id)})
    if not listing_data:
        return jsonify({"error": "Listing not found"}), 404
    
    listing = Listing(**listing_data)
    
    # Check if there's already a draft
    existing_draft = db.communications.find_one({
        "user_id": ObjectId(session['user_id']),
        "listing_id": ObjectId(listing_id),
        "direction": "outgoing",
        "status": "draft"
    })
    
    if existing_draft:
        return jsonify({
            "message": "Draft already exists",
            "communication": {
                "id": str(existing_draft["_id"]),
                "subject": existing_draft["subject"],
                "content": existing_draft["content"],
                "recipient": existing_draft["recipient"],
                "created_at": existing_draft["created_at"]
            }
        })
    
    # Get email type from request
    data = request.get_json()
    email_type = data.get('type', 'initial_outreach')
    
    # Create appropriate draft based on type
    if email_type == 'initial_outreach':
        communication = email_service.create_initial_contact_email(user, listing)
    elif email_type == 'follow_up':
        # Find the initial contact date
        initial_comm = db.communications.find_one({
            "user_id": ObjectId(session['user_id']),
            "listing_id": ObjectId(listing_id),
            "direction": "outgoing",
            "status": "sent"
        }, sort=[("created_at", 1)])
        
        initial_date = initial_comm.get("sent_at") if initial_comm else datetime.utcnow()
        
        communication = email_service.create_follow_up_email(user, listing, initial_date)
    else:
        return jsonify({"error": "Invalid email type"}), 400
    
    if not communication:
        return jsonify({"error": "Failed to create email draft"}), 500
    
    return jsonify({
        "message": "Draft created successfully",
        "communication": {
            "id": str(communication._id),
            "subject": communication.subject,
            "content": communication.content,
            "recipient": communication.recipient,
            "created_at": communication.created_at
        }
    })

@communications_bp.route('/<communication_id>', methods=['PUT'])
def update_communication(communication_id):
    """Update a communication draft"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get communication
    comm_data = db.communications.find_one({
        "_id": ObjectId(communication_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not comm_data:
        return jsonify({"error": "Communication not found"}), 404
    
    # Make sure it's a draft
    if comm_data.get("status") != "draft":
        return jsonify({"error": "Only drafts can be updated"}), 400
    
    # Update fields
    data = request.get_json()
    
    update_data = {}
    if 'subject' in data:
        update_data["subject"] = data['subject']
    if 'content' in data:
        update_data["content"] = data['content']
    if 'recipient' in data:
        update_data["recipient"] = data['recipient']
    
    if update_data:
        db.communications.update_one(
            {"_id": ObjectId(communication_id)},
            {"$set": update_data}
        )
    
    # Get updated communication
    updated_comm = db.communications.find_one({"_id": ObjectId(communication_id)})
    
    return jsonify({
        "message": "Communication updated successfully",
        "communication": {
            "id": str(updated_comm["_id"]),
            "subject": updated_comm["subject"],
            "content": updated_comm["content"],
            "recipient": updated_comm["recipient"],
            "created_at": updated_comm["created_at"]
        }
    })

@communications_bp.route('/<communication_id>/send', methods=['POST'])
def send_communication(communication_id):
    """Send a communication"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get communication
    comm_data = db.communications.find_one({
        "_id": ObjectId(communication_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not comm_data:
        return jsonify({"error": "Communication not found"}), 404
    
    # Make sure it's a draft
    if comm_data.get("status") != "draft":
        return jsonify({"error": "Only drafts can be sent"}), 400
    
    # Send the email
    success = email_service.send_email(ObjectId(communication_id))
    
    if not success:
        return jsonify({"error": "Failed to send email"}), 500
    
    return jsonify({
        "message": "Email sent successfully",
        "communication_id": communication_id
    })

@communications_bp.route('/inbox', methods=['GET'])
def get_communications():
    """Get all communications for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Parse query parameters
    listing_id = request.args.get('listing_id')
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Build query
    query = {"user_id": ObjectId(session['user_id'])}
    
    if listing_id:
        query["listing_id"] = ObjectId(listing_id)
    
    if status:
        query["status"] = status
    
    # Get communications
    communications = list(db.communications.find(query)
                         .sort("created_at", -1)
                         .skip(skip)
                         .limit(limit))
    
    # Format for response
    result = []
    for comm in communications:
        listing = db.listings.find_one({"_id": comm["listing_id"]})
        
        result.append({
            "id": str(comm["_id"]),
            "listing_id": str(comm["listing_id"]),
            "listing_address": listing["address"] if listing else "Unknown",
            "direction": comm["direction"],
            "type": comm["type"],
            "subject": comm["subject"],
            "status": comm["status"],
            "created_at": comm["created_at"],
            "sent_at": comm.get("sent_at")
        })
    
    return jsonify({
        "communications": result,
        "count": len(result)
    })

@communications_bp.route('/<communication_id>', methods=['GET'])
def get_communication(communication_id):
    """Get a specific communication"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get communication
    comm_data = db.communications.find_one({
        "_id": ObjectId(communication_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not comm_data:
        return jsonify({"error": "Communication not found"}), 404
    
    communication = Communication(**comm_data)
    
    return jsonify({
        "id": str(communication._id),
        "listing_id": str(communication.listing_id),
        "direction": communication.direction,
        "type": communication.type,
        "subject": communication.subject,
        "content": communication.content,
        "recipient": communication.recipient,
        "sender": communication.sender,
        "status": communication.status,
        "created_at": communication.created_at,
        "sent_at": communication.sent_at,
        "analysis": communication.analysis
    })