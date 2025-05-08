from datetime import datetime
from app import db
from bson.objectid import ObjectId

class Listing:
    """Listing model for rental properties"""
    
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.external_id = kwargs.get('external_id')
        self.source = kwargs.get('source')
        self.title = kwargs.get('title')
        self.description = kwargs.get('description')
        self.price = kwargs.get('price')
        self.bedrooms = kwargs.get('bedrooms')
        self.bathrooms = kwargs.get('bathrooms')
        self.address = kwargs.get('address')
        self.url = kwargs.get('url')
        self.image_url = kwargs.get('image_url')
        self.available_from = kwargs.get('available_from')
        self.property_type = kwargs.get('property_type')
        self.contact_info = kwargs.get('contact_info', {})
        self.metadata = kwargs.get('metadata', {})
        self.date_found = kwargs.get('date_found', datetime.utcnow())
        self.last_updated = kwargs.get('last_updated', datetime.utcnow())
        self.status = kwargs.get('status', 'active')
    
    @classmethod
    def find_by_id(cls, listing_id):
        """Find listing by ID"""
        listing_data = db.listings.find_one({"_id": ObjectId(listing_id)})
        if listing_data:
            return cls(**listing_data)
        return None
    
    @classmethod
    def find_by_external_id(cls, external_id):
        """Find listing by external ID"""
        listing_data = db.listings.find_one({"external_id": external_id})
        if listing_data:
            return cls(**listing_data)
        return None
    
    @classmethod
    def find_active_listings(cls, filters=None, limit=20, skip=0):
        """Find active listings with optional filters"""
        query = {"status": "active"}
        if filters:
            query.update(filters)
        
        cursor = db.listings.find(query).sort("date_found", -1).skip(skip).limit(limit)
        return [cls(**listing) for listing in cursor]
    
    def save(self):
        """Save listing to database"""
        self.last_updated = datetime.utcnow()
        if not self._id:
            # New listing
            document = {
                "external_id": self.external_id,
                "source": self.source,
                "title": self.title,
                "description": self.description,
                "price": self.price,
                "bedrooms": self.bedrooms,
                "bathrooms": self.bathrooms,
                "address": self.address,
                "url": self.url,
                "image_url": self.image_url,
                "available_from": self.available_from,
                "property_type": self.property_type,
                "contact_info": self.contact_info,
                "metadata": self.metadata,
                "date_found": self.date_found,
                "last_updated": self.last_updated,
                "status": self.status
            }
            result = db.listings.insert_one(document)
            self._id = result.inserted_id
        else:
            # Update existing listing
            db.listings.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "title": self.title,
                    "description": self.description,
                    "price": self.price,
                    "bedrooms": self.bedrooms,
                    "bathrooms": self.bathrooms,
                    "address": self.address,
                    "url": self.url,
                    "image_url": self.image_url,
                    "available_from": self.available_from, 
                    "property_type": self.property_type,
                    "contact_info": self.contact_info,
                    "metadata": self.metadata,
                    "last_updated": self.last_updated,
                    "status": self.status
                }}
            )
        
        return self
    
    def to_dict(self):
        """Convert listing to dictionary"""
        return {
            "id": str(self._id),
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "address": self.address,
            "url": self.url,
            "image_url": self.image_url,
            "available_from": self.available_from,
            "property_type": self.property_type,
            "date_found": self.date_found,
            "status": self.status
        }