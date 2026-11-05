"""Load test with Locust (Member 4).

Each simulated user registers, joins a shared group, then repeatedly browses
the feed, searches, opens photos, comments and sometimes uploads.

  pip install locust
  locust -f locustfile.py --host http://<EC2-PUBLIC-IP>
  then open http://localhost:8089, e.g. 50 users, spawn rate 5

Headless (saves CSV + HTML report for the report appendix):
  locust -f locustfile.py --host http://<EC2-PUBLIC-IP> --headless -u 50 -r 5 -t 3m \
         --csv results/locust --html results/locust_report.html
"""
import io
import random
import uuid

from locust import HttpUser, between, events, task

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)
SHARED = {}


@events.test_start.add_listener
def create_shared_group(environment, **kwargs):
    """One owner account creates a group that every simulated user joins."""
    import requests

    host = environment.host.rstrip("/")
    name = f"owner_{uuid.uuid4().hex[:8]}"
    r = requests.post(f"{host}/api/auth/register", json={"username": name, "email": f"{name}@test.com", "password": "secret123"})
    SHARED["owner_headers"] = {"Authorization": f"Bearer {r.json()['token']}"}
    g = requests.post(f"{host}/api/groups", headers=SHARED["owner_headers"], json={"name": "Locust load test"})
    SHARED["group_id"] = g.json()["id"]


class PhotoShareUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        import requests

        self.username = f"lc_{uuid.uuid4().hex[:10]}"
        r = self.client.post("/api/auth/register", name="/api/auth/register",
                             json={"username": self.username, "email": f"{self.username}@test.com", "password": "secret123"})
        self.headers = {"Authorization": f"Bearer {r.json()['token']}"}
        requests.post(f"{self.host.rstrip('/')}/api/groups/{SHARED['group_id']}/members",
                      headers=SHARED["owner_headers"], json={"username": self.username})
        self.photo_ids = []

    @task(5)
    def browse_feed(self):
        r = self.client.get("/api/photos", headers=self.headers, params={"per_page": 12}, name="/api/photos [feed]")
        if r.ok:
            self.photo_ids = [p["id"] for p in r.json()["items"]] or self.photo_ids

    @task(2)
    def search(self):
        self.client.get("/api/photos", headers=self.headers,
                        params={"q": random.choice(["beach", "load", "comment", "trip"])}, name="/api/photos [search]")

    @task(3)
    def view_photo(self):
        if self.photo_ids:
            self.client.get(f"/api/photos/{random.choice(self.photo_ids)}", headers=self.headers, name="/api/photos/[id]")

    @task(2)
    def comment(self):
        if self.photo_ids:
            self.client.post(f"/api/photos/{random.choice(self.photo_ids)}/comments", headers=self.headers,
                             json={"content": f"Nice one from {self.username}"}, name="/api/photos/[id]/comments")

    @task(1)
    def upload(self):
        self.client.post("/api/photos", headers=self.headers, name="/api/photos [upload]",
                         data={"group_id": SHARED["group_id"], "caption": "load test", "tags": "load,trip"},
                         files={"photo": ("test.png", io.BytesIO(PNG), "image/png")})
