# AWS Deployment Guide (Member 4, with Member 3 for RDS and S3)

Region used in this guide: **Asia Pacific (Singapore) `ap-southeast-1`**, the closest common region to Malaysia.

## Target architecture

```
 Users' browsers
        │  HTTP :80
        ▼
┌──────────────────────── EC2 (t3.micro, Ubuntu 24.04) ────────────────────────┐
│  nginx  ── serves React build (presentation tier)                            │
│    │                                                                         │
│    └─ /api/* ──► Gunicorn (3 workers) ──► Flask REST API (application tier)  │
└──────────────────────────────┬──────────────────────────────┬────────────────┘
                               │ SQL :5432 (private)          │ boto3 (IAM role)
                               ▼                              ▼
                 RDS PostgreSQL (db.t3/t4g.micro)     S3 bucket (private)
                 users, groups, photos metadata,     photo files
                 comments  (data tier)               (storage tier)
```

## Step 0: Protect the budget first (do this before anything else)

1. Billing and Cost Management → **Budgets** → Create budget → "Zero spend budget" or a monthly budget of USD 5, with an email alert to all four members.
2. Note which AWS plan the account is on. Accounts created on or after 15 July 2025 choose a **Free plan** (credit-based, up to 6 months) or a **Paid plan** at sign-up. Older accounts keep the legacy 12-month free tier. Check *Billing → Credits* for your remaining credits and end date.
3. Only use micro-size instances. Stop or delete everything after the demo video is recorded.

## Step 1: S3 bucket (photo storage)

1. S3 → Create bucket, name e.g. `photoshare-teb3033-<groupname>` (must be globally unique), region `ap-southeast-1`.
2. Keep **Block all public access = ON**. The app uses presigned URLs, so the bucket never needs to be public.
3. Default encryption: SSE-S3 (default).
4. Optional cost saving: Management → Lifecycle rule to delete objects after 30 days.

## Step 2: IAM role for EC2 (no access keys in code)

1. IAM → Policies → Create policy → JSON → paste `deploy/s3-access-policy.json` (replace the bucket name). Name: `PhotoShareS3Access`.
2. IAM → Roles → Create role → Trusted entity: **EC2** → attach `PhotoShareS3Access`. Name: `PhotoShareEC2Role`.

## Step 3: Security groups

| Name | Inbound rules |
|---|---|
| `photoshare-web-sg` (EC2) | HTTP 80 from 0.0.0.0/0; SSH 22 from **My IP** only |
| `photoshare-db-sg` (RDS) | PostgreSQL 5432 from **`photoshare-web-sg`** only (not from the internet) |

## Step 4: RDS PostgreSQL (database)

1. RDS → Create database → Standard create → PostgreSQL (latest 16/17).
2. Template: **Free tier** (if shown) or Dev/Test. Instance: `db.t4g.micro` or `db.t3.micro`. Single-AZ. Storage: 20 GB gp3, **storage autoscaling OFF**.
3. DB identifier `photoshare-db`, master username `photoshare_admin`, set a strong password.
4. Connectivity: Public access **No**, security group `photoshare-db-sg`.
5. Additional configuration → Initial database name: `photoshare`. Backups: 1 day. Turn off Performance Insights and enhanced monitoring (cost).
6. After it is "Available", copy the **Endpoint**.

`DATABASE_URL=postgresql://photoshare_admin:<PASSWORD>@<ENDPOINT>:5432/photoshare`

## Step 5: EC2 instance (web + API server)

1. EC2 → Launch instance → Ubuntu Server 24.04 LTS, type **t3.micro** (or t2.micro if offered as free-tier eligible).
2. Key pair: create one and keep the `.pem` file safe.
3. Network: security group `photoshare-web-sg`, auto-assign public IP **enabled**.
4. Advanced details → IAM instance profile: **`PhotoShareEC2Role`**.
5. Storage: 8–10 GB gp3.

## Step 6: Install the app

```bash
ssh -i key.pem ubuntu@<EC2-PUBLIC-IP>
sudo mkdir -p /opt/photoshare && sudo chown ubuntu:ubuntu /opt/photoshare
git clone <your-github-repo-url> /opt/photoshare     # or scp the project folder
cd /opt/photoshare/backend
cp .env.example .env && nano .env
```

Set in `.env`:

```
SECRET_KEY=<random>            # python3 -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY=<random>
DATABASE_URL=postgresql://photoshare_admin:<PASSWORD>@<RDS-ENDPOINT>:5432/photoshare
STORAGE_BACKEND=s3
S3_BUCKET=<bucket-name>
AWS_REGION=ap-southeast-1
```

Then:

```bash
cd /opt/photoshare
psql "postgresql://photoshare_admin:<PASSWORD>@<RDS-ENDPOINT>:5432/photoshare" -f backend/database/schema.sql   # optional, the app also creates tables
bash deploy/setup_ec2.sh
```

Open `http://<EC2-PUBLIC-IP>/`. Check `http://<EC2-PUBLIC-IP>/api/health` shows `"database": true` and `"storage": "s3"`.

Optional: allocate an **Elastic IP** so the URL does not change when the instance restarts (note: public IPv4 addresses are charged per hour).

## Step 7: Updating after code changes

```bash
cd /opt/photoshare && bash deploy/update.sh
```

## Troubleshooting

| Problem | Check |
|---|---|
| 502 Bad Gateway | `sudo systemctl status photoshare` and `tail -50 /var/log/photoshare/error.log` |
| Health shows database false | RDS security group allows 5432 from `photoshare-web-sg`; endpoint and password in `.env` |
| Upload fails with AccessDenied | IAM role attached to the instance; bucket name in policy matches `.env` |
| Upload fails with 413 | `client_max_body_size` in nginx and `MAX_UPLOAD_MB` in `.env` |
| Photos do not show | Bucket region matches `AWS_REGION` |

## Optional: show horizontal scaling (extra marks for "distributed")

The API keeps no session state (JWT login), and all data is in RDS and S3. This means a second EC2 instance can run the same code. To demonstrate it:

1. Create an AMI from the working instance and launch a second instance from it.
2. Create an **Application Load Balancer** with both instances in a target group, health check path `/api/health`.
3. Call `/api/health` several times: the `server` field changes between the two hostnames.

An ALB adds hourly cost, so only run it for the test and demo, then delete it.

## Shutdown checklist (after the demo video)

- [ ] Terminate EC2 instance(s) and release any Elastic IP
- [ ] Delete load balancer and target group (if created)
- [ ] Delete RDS instance (skip final snapshot, or keep one and delete later)
- [ ] Empty and delete the S3 bucket
- [ ] Check Billing → Bills the next day to confirm no running charges
