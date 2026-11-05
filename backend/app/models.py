"""Database tables (data tier). Matches database/schema.sql."""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


def iso(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:  # SQLite returns naive datetimes
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, private=False):
        data = {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name or self.username,
        }
        if private:
            data["email"] = self.email
            data["created_at"] = iso(self.created_at)
        return data


class FriendGroup(db.Model):
    __tablename__ = "friend_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    owner = db.relationship("User")
    members = db.relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner.to_dict(),
            "member_count": len(self.members),
            "created_at": iso(self.created_at),
        }


class GroupMember(db.Model):
    __tablename__ = "group_members"
    __table_args__ = (db.UniqueConstraint("group_id", "user_id", name="uq_group_user"),)

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("friend_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False, default="member")  # "owner" or "member"
    joined_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    group = db.relationship("FriendGroup", back_populates="members")
    user = db.relationship("User")

    def to_dict(self):
        return {"user": self.user.to_dict(), "role": self.role, "joined_at": iso(self.joined_at)}


class Photo(db.Model):
    __tablename__ = "photos"

    id = db.Column(db.Integer, primary_key=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("friend_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    storage_key = db.Column(db.String(255), unique=True, nullable=False)  # object key in S3
    original_filename = db.Column(db.String(255))
    content_type = db.Column(db.String(50))
    caption = db.Column(db.Text)
    tags = db.Column(db.String(500), default="")  # lowercase, comma-separated, e.g. "beach,trip"
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    uploader = db.relationship("User")
    group = db.relationship("FriendGroup")
    comments = db.relationship("Comment", back_populates="photo", cascade="all, delete-orphan",
                               order_by="Comment.created_at")

    def tag_list(self):
        return [t for t in (self.tags or "").split(",") if t]

    def to_dict(self, url):
        return {
            "id": self.id,
            "url": url,
            "caption": self.caption,
            "tags": self.tag_list(),
            "uploader": self.uploader.to_dict(),
            "group": {"id": self.group.id, "name": self.group.name},
            "comment_count": len(self.comments),
            "created_at": iso(self.created_at),
        }


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey("photos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True))

    photo = db.relationship("Photo", back_populates="comments")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "photo_id": self.photo_id,
            "user": self.user.to_dict(),
            "content": self.content,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "edited": self.updated_at is not None,
        }
