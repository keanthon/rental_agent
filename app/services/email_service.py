import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from datetime import datetime
from app.api.openai_client import OpenAIClient
from app.models.communication import Communication
from app import db
from app.config import EMAIL_SERVER, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_USE_TLS

class EmailService:
    """Service for handling email communications with landlords/property managers"""
    
    def __init__(self, openai_api_key=None):
        self.openai_client = OpenAIClient(openai_api_key)
        self.email_config = {
            'server': EMAIL_SERVER,
            'port': EMAIL_PORT,
            'username': EMAIL_USERNAME,
            'password': EMAIL_PASSWORD,
            'use_tls': EMAIL_USE_TLS
        }
    
    def create_initial_contact_email(self, user, listing):
        """
        Generate an initial contact email for a rental listing
        
        Args:
            user: User object
            listing: Listing object
            
        Returns:
            Communication: The created communication object (unsent)
        """
        # Prepare context for email generation
        context = {
            'address': listing.address,
            'price': listing.price,
            'bedrooms': listing.bedrooms,
            'bathrooms': listing.bathrooms,
            'user_name': f"{user.first_name} {user.last_name}",
            'move_in_date': user.rental_preferences.get('move_in_date', 'flexible'),
            'occupants': user.rental_preferences.get('occupants', 1),
            'preferred_viewing_date': 'next week'  # Default, could be customized
        }
        
        # Generate email content using OpenAI
        email_content = self.openai_client.generate_email('initial_outreach', context)
        
        if not email_content:
            logging.error("Failed to generate initial contact email")
            return None
        
        # Create a subject line
        subject = f"Inquiry about rental property at {listing.address}"
        
        # Create a new communication record
        communication = Communication(
            user_id=user._id,
            listing_id=listing._id,
            direction='outgoing',
            type='email',
            subject=subject,
            content=email_content,
            recipient=listing.contact_info.get('email'),
            sender=EMAIL_USERNAME,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        # Save to database
        communication.save()
        
        return communication
    
    def create_follow_up_email(self, user, listing, initial_contact_date):
        """
        Generate a follow-up email for a rental listing
        
        Args:
            user: User object
            listing: Listing object
            initial_contact_date: Date of initial contact
            
        Returns:
            Communication: The created communication object (unsent)
        """
        # Prepare context for email generation
        context = {
            'address': listing.address,
            'initial_contact_date': initial_contact_date,
            'user_name': f"{user.first_name} {user.last_name}"
        }
        
        # Generate email content using OpenAI
        email_content = self.openai_client.generate_email('follow_up', context)
        
        if not email_content:
            logging.error("Failed to generate follow-up email")
            return None
        
        # Create a subject line
        subject = f"Follow-up: Inquiry about rental property at {listing.address}"
        
        # Create a new communication record
        communication = Communication(
            user_id=user._id,
            listing_id=listing._id,
            direction='outgoing',
            type='email',
            subject=subject,
            content=email_content,
            recipient=listing.contact_info.get('email'),
            sender=EMAIL_USERNAME,
            status='draft',
            created_at=datetime.utcnow()
        )
        
        # Save to database
        communication.save()
        
        return communication
    
    def send_email(self, communication_id):
        """
        Send an email communication
        
        Args:
            communication_id: ID of the communication to send
            
        Returns:
            bool: Success or failure
        """
        try:
            # Get the communication from the database
            comm_data = db.communications.find_one({"_id": communication_id})
            if not comm_data:
                logging.error(f"Communication {communication_id} not found")
                return False
            
            communication = Communication(**comm_data)
            
            # Prepare the email
            msg = MIMEMultipart()
            msg['From'] = communication.sender
            msg['To'] = communication.recipient
            msg['Subject'] = communication.subject
            msg.attach(MIMEText(communication.content, 'plain'))
            
            # Connect to the SMTP server
            if self.email_config['use_tls']:
                smtp = smtplib.SMTP(self.email_config['server'], self.email_config['port'])
                smtp.starttls()
            else:
                smtp = smtplib.SMTP(self.email_config['server'], self.email_config['port'])
            
            # Login and send the email
            smtp.login(self.email_config['username'], self.email_config['password'])
            smtp.send_message(msg)
            smtp.quit()
            
            # Update the communication status
            communication.mark_as_sent()
            
            # Update the match status if applicable
            match = db.matches.find_one({
                "user_id": communication.user_id,
                "listing_id": communication.listing_id
            })
            
            if match:
                db.matches.update_one(
                    {"_id": match["_id"]},
                    {"$set": {
                        "contacted": True,
                        "status": "contacted",
                        "last_updated": datetime.utcnow()
                    }}
                )
            
            return True
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            return False
    
    def analyze_incoming_email(self, email_content, original_communication_id=None):
        """
        Analyze an incoming email response
        
        Args:
            email_content: Content of the email
            original_communication_id: ID of the original outgoing communication (if available)
            
        Returns:
            dict: Analysis results
        """
        try:
            # Use OpenAI to analyze the email
            analysis = self.openai_client.analyze_email_response(email_content)
            
            if original_communication_id:
                # Update the original communication with the analysis
                db.communications.update_one(
                    {"_id": original_communication_id},
                    {"$set": {
                        "analysis": analysis,
                        "last_updated": datetime.utcnow()
                    }}
                )
            
            return analysis
        except Exception as e:
            logging.error(f"Error analyzing email: {str(e)}")
            return {
                "error": str(e),
                "property_available": None,
                "intent": "error",
                "sentiment": "neutral"
            }