# Multi-User Testing (Member 4)

Two tools are provided. Run both against the deployed URL and keep the output as evidence for Section 6 of the report.

## 1. Concurrency correctness test (`concurrency_test.py`)

Fires requests from many users at the same moment and checks the results are correct.

```bash
pip install requests
python concurrency_test.py --url http://<EC2-PUBLIC-IP> --users 20
python concurrency_test.py --url http://<EC2-PUBLIC-IP> --users 50
```

| Check | What it proves |
|---|---|
| Same-username race: exactly 1 success | The database UNIQUE constraint prevents duplicate accounts under concurrency |
| N concurrent comments, N stored | No lost updates when many users comment on one photo |
| N same-name uploads, N distinct files | UUID storage keys stop users overwriting each other's photos in S3 |
| No 5xx errors | The server stays stable under concurrent load |

Screenshot the terminal output and attach the generated `results_*.csv`.

## 2. Load test (`locustfile.py`)

Simulates realistic users browsing, searching, commenting and uploading.

```bash
pip install locust
locust -f locustfile.py --host http://<EC2-PUBLIC-IP> --headless -u 50 -r 5 -t 3m \
       --csv results/locust --html results/locust_report.html
```

Suggested runs for the report table: 10, 25 and 50 users for 3 minutes each. Record requests per second, average and 95th percentile response time, and failure rate. While each run is going, screenshot **EC2 → Monitoring → CPU utilization** and **RDS → Monitoring → DB connections**.

## 3. Manual multi-device test (for the demo video)

1. Three members log in on different devices (laptop, phone) to the deployed URL, all in the same group.
2. Member A uploads a photo. Members B and C refresh the feed and see it.
3. B and C comment on the photo at the same time. Each photo page refreshes every 10 seconds, so everyone sees the new comments.
4. Show search (keyword, uploader, tag, date) on one device.

## Example result (local run, 20 users, development server)

```
register               n=20   avg= 1038.3 ms  status={201: 20}
duplicate_register     n=20   avg=  827.3 ms  status={201: 1, 409: 19}
comment_same_photo     n=20   avg=   87.5 ms  status={201: 20}
upload_same_name       n=20   avg=  100.5 ms  status={201: 20}
feed_read              n=20   avg=  219.9 ms  status={200: 20}
5/5 checks passed
```

Registration is the slowest step because passwords are hashed with a deliberately slow algorithm (scrypt). This is a security feature, which is worth mentioning in the report. Replace these numbers with your own cloud results.
