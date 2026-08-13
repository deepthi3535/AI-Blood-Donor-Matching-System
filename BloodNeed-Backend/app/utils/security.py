from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Ensure JWT is valid in the request
            verify_jwt_in_request()
            
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.active or user.role not in roles:
                return jsonify({"message": "Forbidden: Access is denied"}), 403
                
            return fn(*args, **kwargs)
        return wrapper
    return decorator
