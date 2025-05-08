import requests
import logging
from app.config import RENTCAST_API_KEY

class RentCastClient:
    BASE_URL = "https://api.rentcast.io/v1"
    
    def __init__(self, api_key=RENTCAST_API_KEY):
        self.api_key = api_key
        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def search_rental_listings(self, params):
        """
        Search for rental listings based on parameters
        
        params: dict containing search parameters such as:
        - location (city, state or zip)
        - minPrice, maxPrice
        - minBedrooms, minBathrooms
        - propertyType
        - status (Active, Pending, etc.)
        """
        try:
            url = f"{self.BASE_URL}/listings/rental/long-term"
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"RentCast API error: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logging.error(f"Response: {e.response.text}")
            return None
    
    def get_listing_details(self, listing_id):
        """Get detailed information about a specific rental listing"""
        try:
            url = f"{self.BASE_URL}/listings/rental/long-term/{listing_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"RentCast API error: {str(e)}")
            return None
    
    def get_market_data(self, zip_code):
        """Get market data for a specific zip code"""
        try:
            url = f"{self.BASE_URL}/markets/{zip_code}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"RentCast API error: {str(e)}")
            return None
    
    def get_rent_estimate(self, address, property_params=None):
        """
        Get rent estimate for a property
        
        address: Property address string
        property_params: Optional dict with additional property details:
            - propertyType
            - bedrooms
            - bathrooms
            - squareFootage
        """
        try:
            url = f"{self.BASE_URL}/valuation/rental/long-term"
            params = {"address": address}
            
            if property_params:
                params.update(property_params)
                
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"RentCast API error: {str(e)}")
            return None