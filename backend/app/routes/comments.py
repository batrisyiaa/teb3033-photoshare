"""Add, view, edit and delete comments on photos."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Comment, Photo, utcnow
from ..utils import ApiError, current_user, get_json, require_member

bp = Blueprint("comments", __name__, url_prefix="/api")

MAX_LEN = 1000


def _content(data):
    content = (data.get("content") or "").strip()
    if not content:
        raise ApiError("Comment cannot be empty")
    if len(content) > MAX_LEN:
        raise ApiError(f"Comment is too long (max {MAX_LEN} characters)")
    return content


def _get_comment(comment_id, user):
    comment = db.session.get(Comment, comment_id)
    if comment is None:
        raise ApiError("Comment not found", 404)
    require_member(comment.photo.group_id, user.id)
    return comment


@bp.get("/photos/<int:photo_id>/comments")
@jwt_required()
def list_comments(photo_id):
    user = current_user()
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        raise ApiError("Photo not found", 404)
    require_member(photo.group_id, user.id)
    return jsonify([c.to_dict() for c in photo.comments])


@bp.post("/photos/<int:photo_id>/comments")
@jwt_required()
def add_comment(photo_id):
    user = current_user()
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        raise ApiError("Photo not found", 404)
    require_member(photo.group_id, user.id)
    # Each comment is its own row (INSERT), so many users can comment on the
    # same photo at the same time without overwriting each other.
    comment = Comment(photo_id=photo.id, user_id=user.id, content=_content(get_json()))
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@bp.put("/comments/<int:comment_id>")
@jwt_required()
def edit_comment(comment_id):
    user = current_user()
    comment = _get_comment(comment_id, user)
    if comment.user_id != user.id:
        raise ApiError("You can only edit your own comments", 403)
    comment.content = _content(get_json())
    comment.updated_at = utcnow()
    db.session.commit()
    return jsonify(comment.to_dict())


@bp.delete("/comments/<int:comment_id>")
@jwt_required()
def delete_comment(comment_id):
    """The comment author or the photo uploader can delete a comment."""
    user = current_user()
    comment = _get_comment(comment_id, user)
    if comment.user_id != user.id and comment.photo.uploader_id != user.id:
        raise ApiError("You can only delete your own comments", 403)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted"})
