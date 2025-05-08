import os
from app import app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
