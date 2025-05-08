import openai
import logging
from app.config import OPENAI_API_KEY

class OpenAIClient:
    def __init__(self, api_key=OPENAI_API_KEY):
        openai.api_key = api_key
    
    def generate_email(self, template_type, context):
        """
        Generate an email using GPT-4
        
        template_type: String indicating email type ('initial_outreach', 'follow_up', etc.)
        context: Dict containing data to include in the email
        """
        prompts = {
            'initial_outreach': f"""
            Write a professional email to inquire about a rental property. Be friendly but concise.
            
            Property details:
            - Address: {context.get('address')}
            - Rent: ${context.get('price')} per month
            - Bedrooms: {context.get('bedrooms')}
            - Bathrooms: {context.get('bathrooms')}
            
            Include the following information about the potential tenant:
            - Name: {context.get('user_name')}
            - Move-in timeframe: {context.get('move_in_date')}
            - Number of occupants: {context.get('occupants', 1)}
            
            Ask these specific questions:
            1. Is the property still available?
            2. Are utilities included in the rent?
            3. What's the parking situation?
            4. Is a viewing possible on {context.get('preferred_viewing_date')}?
            
            End with a polite sign-off and contact information.
            """,
            'follow_up': f"""
            Write a brief follow-up email regarding a rental property inquiry. Be polite but direct.
            
            Initial contact was made on {context.get('initial_contact_date')} about:
            - Address: {context.get('address')}
            
            Mention that you're still interested in the property and would appreciate an update.
            If you haven't received a response yet, ask if the property is still available.
            If you did receive a response but have pending questions, mention those specifically.
            
            Sign off with your name and contact information.
            """,
            'schedule_viewing': f"""
            Write a concise email to confirm a property viewing appointment.
            
            Property details:
            - Address: {context.get('address')}
            
            Viewing details:
            - Date: {context.get('viewing_date')}
            - Time: {context.get('viewing_time')}
            
            Mention that you're looking forward to seeing the property and meeting them.
            Ask if there's any specific information or documents you should bring.
            
            End with a polite sign-off and include your phone number for day-of contact.
            """
        }
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant helping a tenant find rental properties. Write professional, clear, and concise emails."},
                    {"role": "user", "content": prompts.get(template_type, "Write a professional email.")}
                ],
                max_tokens=600,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"OpenAI API error: {str(e)}")
            return None
            
    def analyze_email_response(self, email_content):
        """
        Analyze an email response from a landlord/agent
        
        Returns a dict with extracted information and intent
        """
        try:
            prompt = f"""
            Analyze this email response from a landlord or property manager:
            
            {email_content}
            
            Extract the following information (return null if not found):
            1. Is the property still available? (yes/no/maybe)
            2. Information about utilities
            3. Information about parking
            4. Proposed viewing times/dates
            5. Additional requirements (e.g., application process, deposit)
            6. Contact phone number (if provided)
            
            Also determine:
            - Primary intent of the email (available, unavailable, request_more_info, offer_viewing, other)
            - Overall sentiment (positive, neutral, negative)
            
            Return your analysis as JSON.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes emails and extracts structured information."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.1
            )
            
            # Parse the response as JSON
            import json
            analysis_text = response.choices[0].message.content
            
            # Handle case where GPT might wrap the JSON in ```json ... ``` or similar
            if "```" in analysis_text:
                # Extract the JSON part
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', analysis_text)
                if json_match:
                    analysis_text = json_match.group(1)
            
            analysis = json.loads(analysis_text)
            return analysis
            
        except Exception as e:
            logging.error(f"OpenAI API error in email analysis: {str(e)}")
            return {
                "error": str(e),
                "property_available": None,
                "utilities_info": None,
                "parking_info": None,
                "viewing_times": None,
                "requirements": None,
                "contact_phone": None,
                "intent": "error",
                "sentiment": "neutral"
            }