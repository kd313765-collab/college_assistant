import datetime
from functools import wraps
import jwt
from flask import request, jsonify, g
import config


def make_token(user):
    payload = {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "roll_no": user.get("roll_no"),
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2),
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"error": "Login karo pehle"}), 401
            try:
                data = jwt.decode(header[7:], config.SECRET_KEY, algorithms=["HS256"])
            except Exception:
                return jsonify({"error": "Session expire ho gaya, dobara login karo"}), 401
            if role and data.get("role") != role:
                return jsonify({"error": "Ye kaam sirf %s kar sakta hai" % role}), 403
            g.user = data
            return fn(*args, **kwargs)
        return wrapper
    return decorator
