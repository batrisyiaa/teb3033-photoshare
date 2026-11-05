"""Friend groups. Photos are shared inside a group, so only members see them."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import FriendGroup, GroupMember, User
from ..utils import ApiError, current_user, get_json, require_member

bp = Blueprint("groups", __name__, url_prefix="/api/groups")


def _get_group(group_id):
    group = db.session.get(FriendGroup, group_id)
    if group is None:
        raise ApiError("Group not found", 404)
    return group


@bp.get("")
@jwt_required()
def list_my_groups():
    user = current_user()
    groups = (
        FriendGroup.query.join(GroupMember)
        .filter(GroupMember.user_id == user.id)
        .order_by(FriendGroup.name)
        .all()
    )
    return jsonify([g.to_dict() for g in groups])


@bp.post("")
@jwt_required()
def create_group():
    user = current_user()
    data = get_json()
    name = (data.get("name") or "").strip()
    if not name or len(name) > 100:
        raise ApiError("Group name is required (max 100 characters)")
    group = FriendGroup(name=name, description=(data.get("description") or "").strip() or None, owner=user)
    group.members.append(GroupMember(user=user, role="owner"))
    db.session.add(group)
    db.session.commit()
    return jsonify(group.to_dict()), 201


@bp.get("/<int:group_id>")
@jwt_required()
def get_group(group_id):
    user = current_user()
    group = _get_group(group_id)
    require_member(group.id, user.id)
    data = group.to_dict()
    data["members"] = [m.to_dict() for m in group.members]
    return jsonify(data)


@bp.post("/<int:group_id>/members")
@jwt_required()
def add_member(group_id):
    """Any member can invite a friend by username."""
    user = current_user()
    group = _get_group(group_id)
    require_member(group.id, user.id)
    username = (get_json().get("username") or "").strip()
    friend = User.query.filter_by(username=username).first()
    if friend is None:
        raise ApiError("No user with that username", 404)
    db.session.add(GroupMember(group_id=group.id, user_id=friend.id, role="member"))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("User is already in this group", 409)
    return jsonify({"message": f"{friend.username} added", "user": friend.to_dict()}), 201


@bp.delete("/<int:group_id>/members/<int:user_id>")
@jwt_required()
def remove_member(group_id, user_id):
    """The owner can remove anyone; a member can remove themselves (leave)."""
    user = current_user()
    group = _get_group(group_id)
    me = require_member(group.id, user.id)
    if user.id != user_id and me.role != "owner":
        raise ApiError("Only the group owner can remove other members", 403)
    if user_id == group.owner_id:
        raise ApiError("The owner cannot leave the group", 400)
    target = GroupMember.query.filter_by(group_id=group.id, user_id=user_id).first()
    if target is None:
        raise ApiError("User is not in this group", 404)
    db.session.delete(target)
    db.session.commit()
    return jsonify({"message": "Member removed"})
