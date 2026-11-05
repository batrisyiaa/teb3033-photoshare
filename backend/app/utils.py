"""Shared helpers: error responses and permission checks."""
from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from .extensions import db
from .models import GroupMember, User


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def error_response(message, status):
    # Every error has the same shape: {"error": "..."}
    return jsonify({"error": message}), status


def current_user():
    user = db.session.get(User, int(get_jwt_identity()))
    if user is None:
        raise ApiError("User not found", 401)
    return user


def membership(group_id, user_id):
    return GroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()


def require_member(group_id, user_id):
    m = membership(group_id, user_id)
    if m is None:
        raise ApiError("You are not a member of this group", 403)
    return m


def user_group_ids(user_id):
    return [m.group_id for m in GroupMember.query.filter_by(user_id=user_id).all()]


def get_json():
    from flask import request

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be JSON")
    return data
