"""Automated API tests. Run from the backend folder:  python -m pytest -v"""
import io

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "STORAGE_BACKEND": "local",
        "LOCAL_UPLOAD_DIR": str(tmp_path / "uploads"),
    })
    # create_app already ran create_all on the default DB URL; make sure the
    # test DB has tables too.
    with app.app_context():
        db.create_all()
    return app.test_client()


def register(client, username):
    r = client.post("/api/auth/register", json={
        "username": username, "email": f"{username}@test.com", "password": "secret123"})
    assert r.status_code == 201, r.get_json()
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def upload(client, headers, group_id, caption="hello", tags="beach, Trip", name="pic.jpg"):
    data = {"photo": (io.BytesIO(b"fake-image-bytes"), name),
            "group_id": str(group_id), "caption": caption, "tags": tags}
    return client.post("/api/photos", headers=headers, data=data, content_type="multipart/form-data")


def test_register_login_and_duplicate(client):
    register(client, "alice")
    r = client.post("/api/auth/register", json={"username": "alice", "email": "x@test.com", "password": "secret123"})
    assert r.status_code == 409
    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrong"})
    assert r.status_code == 401
    r = client.post("/api/auth/login", json={"username": "alice", "password": "secret123"})
    assert r.status_code == 200 and "token" in r.get_json()


def test_requires_login(client):
    assert client.get("/api/photos").status_code == 401


def test_full_flow(client):
    alice = register(client, "alice")
    bob = register(client, "bob")
    carol = register(client, "carol")  # not in the group

    gid = client.post("/api/groups", headers=alice, json={"name": "Trip Squad"}).get_json()["id"]
    assert client.post(f"/api/groups/{gid}/members", headers=alice, json={"username": "bob"}).status_code == 201
    assert client.post(f"/api/groups/{gid}/members", headers=alice, json={"username": "bob"}).status_code == 409

    r = upload(client, alice, gid)
    assert r.status_code == 201
    photo = r.get_json()
    assert photo["tags"] == ["beach", "trip"]
    assert photo["uploader"]["username"] == "alice"

    # Bob (member) sees it; Carol (not a member) does not.
    assert client.get("/api/photos", headers=bob).get_json()["total"] == 1
    assert client.get("/api/photos", headers=carol).get_json()["total"] == 0
    assert client.get(f"/api/photos/{photo['id']}", headers=carol).status_code == 403
    assert upload(client, carol, gid).status_code == 403

    # Comments
    r = client.post(f"/api/photos/{photo['id']}/comments", headers=bob, json={"content": "Nice sunset!"})
    assert r.status_code == 201
    cid = r.get_json()["id"]
    assert client.put(f"/api/comments/{cid}", headers=alice, json={"content": "hack"}).status_code == 403
    r = client.put(f"/api/comments/{cid}", headers=bob, json={"content": "Amazing sunset!"})
    assert r.get_json()["edited"] is True
    detail = client.get(f"/api/photos/{photo['id']}", headers=alice).get_json()
    assert detail["comments"][0]["content"] == "Amazing sunset!"

    # Search and filter (bonus)
    upload(client, bob, gid, caption="lunch", tags="food")
    assert client.get("/api/photos?q=sunset", headers=alice).get_json()["total"] == 1  # comment text
    assert client.get("/api/photos?tag=food", headers=alice).get_json()["total"] == 1
    assert client.get("/api/photos?uploader=bob", headers=alice).get_json()["total"] == 1
    assert client.get("/api/photos?q=alice", headers=alice).get_json()["total"] == 1
    assert client.get("/api/photos?date_from=2000-01-01", headers=alice).get_json()["total"] == 2
    assert client.get("/api/photos?date_to=2000-01-01", headers=alice).get_json()["total"] == 0

    # Delete permissions
    assert client.delete(f"/api/photos/{photo['id']}", headers=bob).status_code == 403
    assert client.delete(f"/api/comments/{cid}", headers=alice).status_code == 200  # photo owner may delete
    assert client.delete(f"/api/photos/{photo['id']}", headers=alice).status_code == 200


def test_rejects_bad_file_type(client):
    alice = register(client, "alice")
    gid = client.post("/api/groups", headers=alice, json={"name": "G"}).get_json()["id"]
    assert upload(client, alice, gid, name="virus.exe").status_code == 400


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.get_json()["database"] is True
