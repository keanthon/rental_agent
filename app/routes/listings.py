from flask import Blueprint, request, jsonify, session
from app.services.matching_service import MatchingService
from app.models.user import User
from app import db
from bson.objectid import ObjectId

listings_bp = Blueprint('listings', __name__, url_prefix='/api/listings')

matching_service = MatchingService()

@listings_bp.route('/matches', methods=['GET'])
def get_matches():
    """Get matched listings for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Parse query parameters
    status = request.args.get('status')
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Get matches for user
    matches = matching_service.get_user_matches(
        session['user_id'], 
        status=status, 
        limit=limit, 
        skip=skip
    )
    
    return jsonify({
        "matches": matches,
        "count": len(matches)
    })

@listings_bp.route('/matches/<match_id>/status', methods=['PUT'])
def update_match_status(match_id):
    """Update the status of a match"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    
    # Make sure the match belongs to the current user
    match = db.matches.find_one({
        "_id": ObjectId(match_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not match:
        return jsonify({"error": "Match not found"}), 404
    
    # Update the match status
    success = matching_service.update_match_status(match_id, new_status)
    
    if success:
        return jsonify({
            "message": "Match status updated successfully",
            "match_id": match_id,
            "status": new_status
        })
    else:
        return jsonify({"error": "Failed to update match status"}), 500

@listings_bp.route('/refresh', methods=['POST'])
def refresh_listings():
    """Manually refresh listings for the current user"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    user_data = db.users.find_one({"_id": ObjectId(session['user_id'])})
    if not user_data:
        session.pop('user_id', None)
        return jsonify({"error": "User not found"}), 404
    
    user = User(**user_data)
    
    # Find new matches for user
    result = matching_service.find_matches_for_user(user)
    
    return jsonify({
        "message": "Listings refreshed successfully",
        "new_matches": result.get("new_listings", 0),
        "errors": result.get("errors", [])
    })

@listings_bp.route('/details/<listing_id>', methods=['GET'])
def get_listing_details(listing_id):
    """Get detailed information about a listing"""
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401
    
    # Get the listing from the database
    listing = db.listings.find_one({"_id": ObjectId(listing_id)})
    
    if not listing:
        return jsonify({"error": "Listing not found"}), 404
    
    # Check if the user has a match for this listing
    match = db.matches.find_one({
        "user_id": ObjectId(session['user_id']),
        "listing_id": ObjectId(listing_id)
    })
    
    if not match:
        return jsonify({"error": "You do not have access to this listing"}), 403
    
    # Update match status to viewed if it's new
    if match.get("status") == "new":
        db.matches.update_one(
            {"_id": match["_id"]},
            {"$set": {
                "status": "viewed",
                "last_updated": db.datetime.utcnow()
            }}
        )
    
    # Get communication history for this listing
    communications = list(db.communications.find({
        "user_id": ObjectId(session['user_id']),
        "listing_id": ObjectId(listing_id)
    }).sort("created_at", -1))
    
    # Format communications for response
    comms_formatted = []
    for comm in communications:
        comms_formatted.append({
            "id": str(comm["_id"]),
            "direction": comm["direction"],
            "type": comm["type"],
            "subject": comm["subject"],
            "content": comm["content"],
            "status": comm["status"],
            "created_at": comm["created_at"],
            "sent_at": comm.get("sent_at")
        })
    
    # Return listing details and communication history
    return jsonify({
        "listing": {
            "id": str(listing["_id"]),
            "external_id": listing["external_id"],
            "source": listing["source"],
            "title": listing.get("title"),
            "description": listing.get("description"),
            "price": listing["price"],
            "bedrooms": listing.get("bedrooms"),
            "bathrooms": listing.get("bathrooms"),
            "address": listing["address"],
            "url": listing.get("url"),
            "image_url": listing.get("image_url"),
            "available_from": listing.get("available_from"),
            "property_type": listing.get("property_type"),
            "date_found": listing["date_found"],
            "contact_info": listing.get("contact_info", {})
        },
        "match": {
            "id": str(match["_id"]),
            "status": match["status"],
            "contacted": match["contacted"],
            "date_matched": match["date_matched"]
        },
        "communications": comms_formatted
    })