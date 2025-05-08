# AI Rental Leasing Agent

An AI-powered application that automates apartment rental searching, communication, and scheduling viewings for users.

## Features

- **User Profiles**: Create and manage user accounts with rental preferences
- **Automated Listing Search**: Automatically search for new rental listings twice daily
- **AI Communication**: Generate and send emails to landlords/property managers
- **Email Analysis**: Analyze email responses from landlords/agents using LLM
- **Dashboard**: User interface for managing listings and communications
- **Scheduling**: Schedule property viewings based on user availability

## Technology Stack

- **Backend**: Python with Flask
- **Database**: MongoDB
- **External APIs**:
  - RentCast API for property listings
  - OpenAI API for email generation and analysis
- **Task Scheduling**: Schedule package for automated searching

## Project Structure

```
ai_rental_agent/
├── app/
│   ├── __init__.py           # Application initialization
│   ├── config.py             # Configuration settings
│   ├── api/                  # External API integrations
│   │   ├── rentcast.py       # RentCast API client
│   │   └── openai_client.py  # OpenAI API client
│   ├── models/               # Database models
│   │   ├── user.py           # User model
│   │   ├── listing.py        # Listing model
│   │   └── communication.py  # Communication model
│   ├── services/             # Business logic services
│   │   ├── listing_service.py   # Listing management
│   │   ├── matching_service.py  # Matching users to listings
│   │   ├── email_service.py     # Email generation and sending
│   │   └── scheduler.py         # Background task scheduling
│   ├── routes/               # API endpoints
│   │   ├── auth.py           # Authentication routes
│   │   ├── profile.py        # User profile routes
│   │   ├── listings.py       # Listing routes
│   │   └── communications.py # Communication routes
│   └── templates/            # Email templates
│       └── emails/
│           ├── initial_outreach.html
│           └── follow_up.html
├── requirements.txt          # Python dependencies
└── run.py                    # Application entry point
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MongoDB
- RentCast API key
- OpenAI API key

### Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys and configuration
5. Start the application:
   ```
   python run.py
   ```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login a user
- `POST /api/auth/logout` - Logout a user
- `GET /api/auth/user` - Get current user information

### User Profile

- `GET /api/profile` - Get user profile and preferences
- `PUT /api/profile` - Update user profile
- `PUT /api/profile/preferences` - Update user rental preferences
- `PUT /api/profile/password` - Update user password

### Listings

- `GET /api/listings/matches` - Get matched listings for current user
- `PUT /api/listings/matches/{match_id}/status` - Update match status
- `POST /api/listings/refresh` - Manually refresh listings
- `GET /api/listings/details/{listing_id}` - Get detailed listing information

### Communications

- `POST /api/communications/draft/{listing_id}` - Create email draft
- `PUT /api/communications/{communication_id}` - Update communication draft
- `POST /api/communications/{communication_id}/send` - Send communication
- `GET /api/communications/inbox` - Get all communications
- `GET /api/communications/{communication_id}` - Get specific communication

## Scheduled Tasks

The application automatically runs the following scheduled tasks:

- Search for new rental listings at 9:00 AM daily
- Search for new rental listings at 4:00 PM daily

## License

This project is licensed under the MIT License - see the LICENSE file for details.
