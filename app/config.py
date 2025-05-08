import os

# Flask configuration
SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
DEBUG = True

# MongoDB configuration
MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/rental_agent'

# RentCast API configuration
RENTCAST_API_KEY = os.environ.get('RENTCAST_API_KEY') or 'your-rentcast-api-key-here'

# Email service configuration
EMAIL_SERVER = os.environ.get('EMAIL_SERVER') or 'smtp.gmail.com'
EMAIL_PORT = int(os.environ.get('EMAIL_PORT') or 587)
EMAIL_USERNAME = os.environ.get('EMAIL_USERNAME') or 'your-email@gmail.com'
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD') or 'your-email-password'
EMAIL_USE_TLS = True

# OpenAI API configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-openai-api-key-here'