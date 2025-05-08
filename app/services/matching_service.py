import logging
from datetime import datetime
from app.services.listing_service import ListingService
from app.models.user import User
from app import db
from bson.objectid import ObjectId

class MatchingService:
    """Service for matching users with rental listings"""
    
    def __init__(self, api_key=None):
        self.listing_service = ListingService(api_key)
    
    def find_matches_for_all_users(self):
        """
        Find new listings for all users based on their preferences
        
        Returns:
            dict: Result with total counts and user-specific results
        """
        logging.info("Starting batch matching for all users")
        
        result = {
            "total_users": 0,
            "total_new_matches": 0,
            "user_results": []
        }
        
        # Get all users from the database
        users_cursor = db.users.find({})
        
        for user_data in users_cursor:
            user = User(**user_data)
            user_result = self.find_matches_for_user(user)
            
            result["total_users"] += 1
            result["total_new_matches"] += user_result.get("new_listings", 0)
            result["user_results"].append({
                "user_id": str(user._id),
                "email": user.email,
                "new_matches": user_result.get("new_listings", 0),
                "errors": user_result.get("errors", [])
            })
        
        logging.info(f"Batch matching completed. Found {result['total_new_matches']} new matches for {result['total_users']} users")
        return result
    
    def find_matches_for_user(self, user):
        """
        Find new rental listings for a specific user
        
        Args:
            user: User object
            
        Returns:
            dict: Result with counts and any errors
        """
        return self.listing_service.fetch_listings_for_user(user)
    
    def get_user_matches(self, user_id, status=None, limit=20, skip=0):
        """
        Get matches for a specific user
        
        Args:
            user_id: User ID
            status: Optional filter by match status
            limit: Max number of results to return
            skip: Number of results to skip (for pagination)
            
        Returns:
            list: Match results with listing data
        """
        return self.listing_service.get_matches_for_user(user_id, status, limit, skip)
    
    def update_match_status(self, match_id, new_status):
        """
        Update the status of a match
        
        Args:
            match_id: Match ID
            new_status: New status (new, viewed, contacted, viewing_scheduled, rejected)
            
        Returns:
            bool: Success or failure
        """
        try:
            db.matches.update_one(
                {"_id": ObjectId(match_id)},
                {"$set": {
                    "status": new_status,
                    "last_updated": datetime.utcnow()
                }}
            )
            return True
        except Exception as e:
            logging.error(f"Error updating match status: {str(e)}")
            return False
    
    def mark_match_contacted(self, match_id, contacted=True):
        """
        Mark a match as contacted or not contacted
        
        Args:
            match_id: Match ID
            contacted: Whether the match has been contacted
            
        Returns:
            bool: Success or failure
        """
        try:
            db.matches.update_one(
                {"_id": ObjectId(match_id)},
                {"$set": {
                    "contacted": contacted,
                    "last_updated": datetime.utcnow()
                }}
            )
            return True
        except Exception as e:
            logging.error(f"Error marking match as contacted: {str(e)}")
            return False