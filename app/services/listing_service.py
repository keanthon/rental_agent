import logging
from datetime import datetime
from app.api.rentcast import RentCastClient
from app.models.listing import Listing
from app import db
from bson.objectid import ObjectId

class ListingService:
    """Service for fetching and managing rental listings"""
    
    def __init__(self, api_key=None):
        self.rentcast_client = RentCastClient(api_key)
    
    def map_user_preferences_to_api_params(self, user_preferences):
        """
        Convert user preferences to RentCast API parameters
        """
        params = {}
        
        # Map location preferences
        if user_preferences.get('location'):
            params['location'] = user_preferences['location']
        
        # Map price range
        if user_preferences.get('min_price'):
            params['minPrice'] = user_preferences['min_price']
        if user_preferences.get('max_price'):
            params['maxPrice'] = user_preferences['max_price']
        
        # Map room specifications
        if user_preferences.get('min_bedrooms'):
            params['minBedrooms'] = user_preferences['min_bedrooms']
        if user_preferences.get('min_bathrooms'):
            params['minBathrooms'] = user_preferences['min_bathrooms']
        
        # Map property type
        if user_preferences.get('property_types'):
            # RentCast expects property types as comma-separated values
            params['propertyType'] = ','.join(user_preferences['property_types'])
        
        # Set to include only active listings
        params['status'] = 'Active'
        
        # Set pagination parameters (limit of up to 500 per request)
        params['limit'] = 100
        params['offset'] = 0
        
        return params
    
    def fetch_listings_for_user(self, user):
        """
        Fetch listings for a specific user based on their preferences
        
        Returns:
            dict: Result with counts and any errors
        """
        logging.info(f"Fetching listings for user {user._id}")
        
        result = {
            "new_listings": 0,
            "errors": []
        }
        
        # Make sure user has preferences set
        if not hasattr(user, 'rental_preferences') or not user.rental_preferences:
            error_msg = f"User {user._id} has no rental preferences set"
            logging.warning(error_msg)
            result["errors"].append(error_msg)
            return result
        
        # Convert user preferences to API parameters
        params = self.map_user_preferences_to_api_params(user.rental_preferences)
        
        # Fetch listings from RentCast API
        api_response = self.rentcast_client.search_rental_listings(params)
        
        if not api_response or not api_response.get('data'):
            error_msg = "No listings found or API error"
            logging.warning(error_msg)
            result["errors"].append(error_msg)
            return result
        
        # Process each listing
        new_matches_count = 0
        for listing_data in api_response.get('data', []):
            # Check if listing already exists in our database
            existing_listing = db.listings.find_one({
                "external_id": listing_data.get('id')
            })
            
            if existing_listing:
                # Listing already exists, update it if needed
                self._update_existing_listing(existing_listing, listing_data)
            else:
                # Create new listing and match
                new_listing_id = self._create_new_listing(listing_data)
                if new_listing_id:
                    # Create match between user and listing
                    self._create_match(user._id, new_listing_id)
                    new_matches_count += 1
        
        result["new_listings"] = new_matches_count
        logging.info(f"Found {new_matches_count} new matches for user {user._id}")
        
        return result
    
    def _update_existing_listing(self, existing_listing, new_data):
        """Update an existing listing with new data"""
        # Check if any important fields have changed
        update_needed = False
        fields_to_check = ['price', 'status', 'description']
        
        for field in fields_to_check:
            if field in new_data and existing_listing.get(field) != new_data.get(field):
                update_needed = True
                break
        
        if update_needed:
            db.listings.update_one(
                {"_id": existing_listing["_id"]},
                {"$set": {
                    "price": new_data.get('price'),
                    "status": new_data.get('status'),
                    "description": new_data.get('description'),
                    "last_updated": datetime.utcnow(),
                    "metadata": new_data
                }}
            )
            logging.info(f"Updated listing {existing_listing['_id']}")
    
    def _create_new_listing(self, listing_data):
        """Create a new listing from API data"""
        try:
            listing_doc = {
                "external_id": listing_data.get('id'),
                "source": "rentcast",
                "title": f"{listing_data.get('bedrooms', 'Studio')} {listing_data.get('propertyType', 'Property')} for Rent",
                "description": listing_data.get('description'),
                "price": listing_data.get('price'),
                "bedrooms": listing_data.get('bedrooms'),
                "bathrooms": listing_data.get('bathrooms'),
                "address": listing_data.get('address', {}).get('full'),
                "url": listing_data.get('listingUrl'),
                "image_url": listing_data.get('photos', [{}])[0].get('url') if listing_data.get('photos') else None,
                "property_type": listing_data.get('propertyType'),
                "available_from": listing_data.get('availableDate'),
                "contact_info": {
                    "email": listing_data.get('contactEmail'),
                    "phone": listing_data.get('contactPhone'),
                    "name": listing_data.get('contactName')
                },
                "date_found": datetime.utcnow(),
                "last_updated": datetime.utcnow(),
                "status": "active",
                "metadata": listing_data
            }
            
            result = db.listings.insert_one(listing_doc)
            return result.inserted_id
        except Exception as e:
            logging.error(f"Error creating new listing: {str(e)}")
            return None
    
    def _create_match(self, user_id, listing_id):
        """Create a match between user and listing"""
        try:
            match = {
                "user_id": user_id,
                "listing_id": listing_id,
                "date_matched": datetime.utcnow(),
                "status": "new",
                "contacted": False,
                "user_notified": False
            }
            
            db.matches.insert_one(match)
            return True
        except Exception as e:
            logging.error(f"Error creating match: {str(e)}")
            return False
    
    def get_matches_for_user(self, user_id, status=None, limit=20, skip=0):
        """Get matches for a specific user"""
        query = {"user_id": ObjectId(user_id)}
        
        if status:
            query["status"] = status
        
        matches = list(db.matches.find(query).sort("date_matched", -1).skip(skip).limit(limit))
        
        # Load associated listings
        result = []
        for match in matches:
            listing = db.listings.find_one({"_id": match["listing_id"]})
            if listing:
                result.append({
                    "match_id": str(match["_id"]),
                    "match_status": match["status"],
                    "contacted": match["contacted"],
                    "date_matched": match["date_matched"],
                    "listing": Listing(**listing).to_dict()
                })
        
        return result