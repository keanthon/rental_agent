from datetime import datetime
from app import db
from bson.objectid import ObjectId

class Communication:
    """Communication model for emails and messages with landlords/agents"""
    
    def __init__(self, **kwargs):
        self._id = kwargs.get('_id')
        self.user_id = kwargs.get('user_id')
        self.listing_id = kwargs.get('listing_id')
        self.direction = kwargs.get('direction')  # 'outgoing' or 'incoming'
        self.type = kwargs.get('type', 'email')  # 'email', 'sms', etc.
        self.subject = kwargs.get('subject')
        self.content = kwargs.get('content')
        self.recipient = kwargs.get('recipient')
        self.sender = kwargs.get('sender')
        self.status = kwargs.get('status', 'draft')  # 'draft', 'sent', 'delivered', 'failed'
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.sent_at = kwargs.get('sent_at')
        self.metadata = kwargs.get('metadata', {})
        self.analysis = kwargs.get('analysis', {})  # For AI analysis of messages
    
    @classmethod
    def find_by_id(cls, communication_id):
        """Find communication by ID"""
        comm_data = db.communications.find_one({"_id": ObjectId(communication_id)})
        if comm_data:
            return cls(**comm_data)
        return None
    
    @classmethod
    def find_for_listing(cls, listing_id, user_id=None):
        """Find all communications for a listing, optionally filtered by user"""
        query = {"listing_id": ObjectId(listing_id)}
        if user_id:
            query["user_id"] = ObjectId(user_id)
        
        cursor = db.communications.find(query).sort("created_at", -1)
        return [cls(**comm) for comm in cursor]
    
    def save(self):
        """Save communication to database"""
        if not self._id:
            # Convert ObjectIds
            if self.user_id and not isinstance(self.user_id, ObjectId):
                self.user_id = ObjectId(self.user_id)
            
            if self.listing_id and not isinstance(self.listing_id, ObjectId):
                self.listing_id = ObjectId(self.listing_id)
                
            # New communication
            document = {
                "user_id": self.user_id,
                "listing_id": self.listing_id,
                "direction": self.direction,
                "type": self.type,
                "subject": self.subject,
                "content": self.content,
                "recipient": self.recipient,
                "sender": self.sender,
                "status": self.status,
                "created_at": self.created_at,
                "sent_at": self.sent_at,
                "metadata": self.metadata,
                "analysis": self.analysis
            }
            result = db.communications.insert_one(document)
            self._id = result.inserted_id
        else:
            # Update existing communication
            db.communications.update_one(
                {"_id": ObjectId(self._id)},
                {"$set": {
                    "direction": self.direction,
                    "type": self.type,
                    "subject": self.subject,
                    "content": self.content,
                    "recipient": self.recipient,
                    "sender": self.sender,
                    "status": self.status,
                    "sent_at": self.sent_at,
                    "metadata": self.metadata,
                    "analysis": self.analysis
                }}
            )
        
        return self
    
    def mark_as_sent(self):
        """Mark communication as sent"""
        self.status = "sent"
        self.sent_at = datetime.utcnow()
        return self.save()
    
    def to_dict(self):
        """Convert communication to dictionary"""
        return {
            "id": str(self._id),
            "user_id": str(self.user_id) if self.user_id else None,
            "listing_id": str(self.listing_id) if self.listing_id else None,
            "direction": self.direction,
            "type": self.type,
            "subject": self.subject,
            "content": self.content,
            "recipient": self.recipient,
            "sender": self.sender,
            "status": self.status,
            "created_at": self.created_at,
            "sent_at": self.sent_at
        }