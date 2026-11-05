"""User registration and login."""
import re

from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, jwt_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..utils import ApiError, current_user, get_json

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,50}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@bp.post("/register")
def register():
    data = get_json()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip() or None

    if not USERNAME_RE.match(username):
        raise ApiError("Username must be 3-50 characters: letters, numbers, _ or .")
    if not EMAIL_RE.match(email):
        raise ApiError("Invalid email address")
    if len(password) < 6:
        raise ApiError("Password must be at least 6 characters")

    user = User(username=username, email=email, display_name=display_name)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # The UNIQUE constraint in the database decides, so two people
        # registering the same name at the same moment cannot both succeed.
        db.session.rollback()
        raise ApiError("Username or email is already taken", 409)

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(private=True)}), 201


@bp.post("/login")
def login():
    data = get_json()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        raise ApiError("Invalid username or password", 401)
    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict(private=True)})


@bp.get("/me")
@jwt_required()
def me():
    return jsonify(current_user().to_dict(private=True))
