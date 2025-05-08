# Import all routes
from app.routes.auth import auth_bp
from app.routes.profile import profile_bp
from app.routes.listings import listings_bp
from app.routes.communications import communications_bp

def register_routes(app):
    """Register all route blueprints with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(communications_bp)