"""Photo upload, feed, search/filter, details and delete."""
import os
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import jwt_required
from sqlalchemy import literal, or_

from ..extensions import db
from ..models import Comment, Photo, User
from ..storage import storage
from ..utils import ApiError, current_user, membership, require_member, user_group_ids

bp = Blueprint("photos", __name__, url_prefix="/api")


def clean_tags(raw):
    """'Beach, #Trip, beach' -> 'beach,trip'"""
    tags = []
    for part in (raw or "").replace(";", ",").split(","):
        tag = part.strip().lstrip("#").lower()[:30]
        if tag and tag not in tags:
            tags.append(tag)
    return ",".join(tags[:10])


def photo_json(photo):
    return photo.to_dict(storage().url(photo.storage_key))


def _get_visible_photo(photo_id, user):
    photo = db.session.get(Photo, photo_id)
    if photo is None:
        raise ApiError("Photo not found", 404)
    require_member(photo.group_id, user.id)
    return photo


def _parse_date(value, name):
    try:
        return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        raise ApiError(f"{name} must be in YYYY-MM-DD format")


@bp.post("/photos")
@jwt_required()
def upload_photo():
    user = current_user()
    file = request.files.get("photo")
    if file is None or not file.filename:
        raise ApiError("No photo file sent (form field name must be 'photo')")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise ApiError("Only jpg, jpeg, png, gif and webp files are allowed")

    try:
        group_id = int(request.form.get("group_id", ""))
    except ValueError:
        raise ApiError("group_id is required")
    require_member(group_id, user.id)

    # A random key means two users uploading "IMG_001.jpg" at the same time
    # never overwrite each other's file.
    key = f"photos/{group_id}/{uuid.uuid4().hex}.{ext}"
    content_type = file.mimetype or f"image/{ext}"
    storage().save(file, key, content_type)

    photo = Photo(
        uploader_id=user.id,
        group_id=group_id,
        storage_key=key,
        original_filename=file.filename[:255],
        content_type=content_type,
        caption=(request.form.get("caption") or "").strip() or None,
        tags=clean_tags(request.form.get("tags")),
    )
    db.session.add(photo)
    try:
        db.session.commit()
    except Exception:
        # Keep storage and database consistent: remove the orphan file.
        db.session.rollback()
        storage().delete(key)
        raise
    return jsonify(photo_json(photo)), 201


@bp.get("/photos")
@jwt_required()
def list_photos():
    """Photo feed with search and filter (bonus feature).

    Query parameters (all optional):
      group_id   only this group
      uploader   username of the uploader
      tag        exact tag
      q          keyword in caption, tags, uploader name or comment text
      date_from  YYYY-MM-DD (inclusive)
      date_to    YYYY-MM-DD (inclusive)
      sort       "newest" (default) or "oldest"
      page, per_page
    """
    user = current_user()
    args = request.args
    groups = user_group_ids(user.id)
    query = Photo.query.filter(Photo.group_id.in_(groups or [-1]))

    if args.get("group_id"):
        try:
            gid = int(args["group_id"])
        except ValueError:
            raise ApiError("group_id must be a number")
        if membership(gid, user.id) is None:
            raise ApiError("You are not a member of this group", 403)
        query = query.filter(Photo.group_id == gid)

    if args.get("uploader"):
        query = query.join(User, Photo.uploader_id == User.id).filter(User.username.ilike(args["uploader"].strip()))

    if args.get("tag"):
        tag = clean_tags(args["tag"]).split(",")[0]
        query = query.filter((literal(",") + Photo.tags + literal(",")).like(f"%,{tag},%"))

    if args.get("q"):
        term = f"%{args['q'].strip()}%"
        comment_match = Comment.query.filter(Comment.photo_id == Photo.id, Comment.content.ilike(term)).exists()
        uploader_match = User.query.filter(
            User.id == Photo.uploader_id,
            or_(User.username.ilike(term), User.display_name.ilike(term)),
        ).exists()
        query = query.filter(or_(Photo.caption.ilike(term), Photo.tags.ilike(term), comment_match, uploader_match))

    if args.get("date_from"):
        query = query.filter(Photo.created_at >= _parse_date(args["date_from"], "date_from"))
    if args.get("date_to"):
        query = query.filter(Photo.created_at < _parse_date(args["date_to"], "date_to") + timedelta(days=1))

    order = Photo.created_at.asc() if args.get("sort") == "oldest" else Photo.created_at.desc()
    query = query.order_by(order, Photo.id.desc())

    page = max(int(args.get("page", 1) or 1), 1)
    per_page = min(max(int(args.get("per_page", 12) or 12), 1), 50)
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "items": [photo_json(p) for p in result.items],
        "page": result.page,
        "per_page": result.per_page,
        "total": result.total,
        "pages": result.pages,
    })


@bp.get("/photos/<int:photo_id>")
@jwt_required()
def get_photo(photo_id):
    user = current_user()
    photo = _get_visible_photo(photo_id, user)
    data = photo_json(photo)
    data["comments"] = [c.to_dict() for c in photo.comments]
    return jsonify(data)


@bp.delete("/photos/<int:photo_id>")
@jwt_required()
def delete_photo(photo_id):
    """The uploader or the group owner can delete a photo."""
    user = current_user()
    photo = _get_visible_photo(photo_id, user)
    if photo.uploader_id != user.id and photo.group.owner_id != user.id:
        raise ApiError("You can only delete your own photos", 403)
    key = photo.storage_key
    db.session.delete(photo)
    db.session.commit()
    storage().delete(key)
    return jsonify({"message": "Photo deleted"})


@bp.get("/files/<path:key>")
def serve_local_file(key):
    """Development only: serves files when STORAGE_BACKEND=local.
    In the cloud, photos come from S3 presigned URLs instead."""
    if current_app.config["STORAGE_BACKEND"] != "local":
        raise ApiError("Not found", 404)
    return send_from_directory(os.path.abspath(current_app.config["LOCAL_UPLOAD_DIR"]), key)
