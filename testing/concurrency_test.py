"""Concurrent multi-user correctness test (Member 4).

It checks that the system behaves correctly when many users act AT THE SAME
TIME, and records response times as evidence for the report.

Scenarios:
  1. N users register at the same time.
  2. N users try to register the SAME username at the same time
     -> exactly one must succeed (database UNIQUE constraint).
  3. N users comment on the SAME photo at the same time
     -> no comment may be lost.
  4. N users upload photos with the SAME file name at the same time
     -> every upload gets its own file, none overwritten.
  5. N users load the feed at the same time.

Usage:
  pip install requests
  python concurrency_test.py --url http://<EC2-PUBLIC-IP> --users 20
Results are printed and saved to results_<timestamp>.csv
"""
import argparse
import csv
import io
import statistics
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

RESULTS = []
LOCK = threading.Lock()

# Tiny valid 1x1 PNG
PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


def timed(scenario, func, *args, **kwargs):
    start = time.perf_counter()
    try:
        resp = func(*args, timeout=60, **kwargs)
        status = resp.status_code
    except requests.RequestException as exc:
        resp, status = None, f"ERR {type(exc).__name__}"
    ms = (time.perf_counter() - start) * 1000
    with LOCK:
        RESULTS.append({"scenario": scenario, "status": status, "ms": round(ms, 1)})
    return resp


def run_parallel(n, fn):
    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(fn, range(n)))


def summary(scenario):
    rows = [r for r in RESULTS if r["scenario"] == scenario]
    times = sorted(r["ms"] for r in rows)
    codes = {}
    for r in rows:
        codes[r["status"]] = codes.get(r["status"], 0) + 1
    p95 = times[max(int(len(times) * 0.95) - 1, 0)]
    print(f"  {scenario:<22} n={len(rows):<4} avg={statistics.mean(times):7.1f} ms  "
          f"p95={p95:7.1f} ms  max={times[-1]:7.1f} ms  status={codes}")


def check(label, ok):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:5000", help="base URL, e.g. http://1.2.3.4")
    ap.add_argument("--users", type=int, default=20)
    args = ap.parse_args()
    api = args.url.rstrip("/") + "/api"
    n = args.users
    run = uuid.uuid4().hex[:6]
    print(f"Target: {api}   concurrent users: {n}   run id: {run}\n")

    # 1. Concurrent registration
    def register(i):
        r = timed("register", requests.post, f"{api}/auth/register",
                  json={"username": f"load_{run}_{i}", "email": f"load_{run}_{i}@test.com", "password": "secret123"})
        return r.json()["token"] if r is not None and r.status_code == 201 else None

    tokens = run_parallel(n, register)
    headers = [{"Authorization": f"Bearer {t}"} for t in tokens if t]

    # 2. Same username race
    def race(i):
        return timed("duplicate_register", requests.post, f"{api}/auth/register",
                     json={"username": f"race_{run}", "email": f"race_{run}_{i}@test.com", "password": "secret123"})

    race_codes = [r.status_code if r is not None else None for r in run_parallel(n, race)]

    # Setup: one group with everyone, one photo
    owner = headers[0]
    gid = requests.post(f"{api}/groups", headers=owner, json={"name": f"Load test {run}"}).json()["id"]
    for i in range(1, len(headers)):
        requests.post(f"{api}/groups/{gid}/members", headers=owner, json={"username": f"load_{run}_{i}"})
    photo_id = requests.post(f"{api}/photos", headers=owner, data={"group_id": gid, "caption": "target"},
                             files={"photo": ("same.png", io.BytesIO(PNG), "image/png")}).json()["id"]

    # 3. Concurrent comments on one photo
    def comment(i):
        return timed("comment_same_photo", requests.post, f"{api}/photos/{photo_id}/comments",
                     headers=headers[i % len(headers)], json={"content": f"comment {i} from user {i}"})

    run_parallel(n, comment)
    comments = requests.get(f"{api}/photos/{photo_id}/comments", headers=owner).json()

    # 4. Concurrent uploads with the same file name
    def upload(i):
        return timed("upload_same_name", requests.post, f"{api}/photos", headers=headers[i % len(headers)],
                     data={"group_id": gid, "caption": f"upload {i}", "tags": "loadtest"},
                     files={"photo": ("IMG_0001.png", io.BytesIO(PNG), "image/png")})

    uploads = [r.json() for r in run_parallel(n, upload) if r is not None and r.status_code == 201]
    urls = {u["url"].split("?")[0] for u in uploads}

    # 5. Concurrent feed reads
    def feed(i):
        return timed("feed_read", requests.get, f"{api}/photos", headers=headers[i % len(headers)],
                     params={"group_id": gid, "per_page": 12})

    run_parallel(n, feed)

    print("Response times")
    for s in ["register", "duplicate_register", "comment_same_photo", "upload_same_name", "feed_read"]:
        summary(s)

    print("\nCorrectness checks")
    results = [
        check(f"{n} users registered concurrently ({len(headers)} succeeded)", len(headers) == n),
        check(f"same-username race: exactly 1 success, {race_codes.count(409)} rejected with 409",
              race_codes.count(201) == 1 and race_codes.count(409) == n - 1),
        check(f"{n} concurrent comments -> {len(comments)} stored (none lost)", len(comments) == n),
        check(f"{n} concurrent same-name uploads -> {len(urls)} distinct stored files", len(uploads) == n and len(urls) == n),
        check("no server errors (5xx) or timeouts",
              not any(str(r["status"]).startswith(("5", "ERR")) for r in RESULTS)),
    ]

    out = f"results_{datetime.now():%Y%m%d_%H%M%S}.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["scenario", "status", "ms"])
        w.writeheader()
        w.writerows(RESULTS)
    print(f"\n{sum(results)}/{len(results)} checks passed. Raw timings saved to {out}")


if __name__ == "__main__":
    main()
