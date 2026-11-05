# Cost Estimate Template (Member 4, report Section 7)

Prices change and differ by region, so fill in the rates from the **AWS Pricing Calculator** (calculator.aws) for `ap-southeast-1`, then confirm with your real bill (**Billing → Bills** and **Cost Explorer**). Screenshot both for the report.

## 1. Monthly estimate (one month, running 24/7)

| Service | Configuration | Unit rate (from calculator) | Usage per month | Monthly cost (USD) |
|---|---|---|---|---|
| EC2 | 1 × t3.micro, Linux, on-demand | $____ / hour | 730 hours | |
| EBS | 10 GB gp3 | $____ / GB-month | 10 GB | |
| Public IPv4 address | 1 address | $____ / hour | 730 hours | |
| RDS PostgreSQL | db.t4g.micro, Single-AZ | $____ / hour | 730 hours | |
| RDS storage | 20 GB gp3 | $____ / GB-month | 20 GB | |
| S3 storage | Standard | $____ / GB-month | e.g. 2 GB | |
| S3 requests | PUT and GET | $____ per 1,000 | e.g. 5k PUT, 50k GET | |
| Data transfer out | Internet | $____ / GB | e.g. 5 GB | |
| **Total (list price)** | | | | |
| Free-tier credits / allowance applied | | | | − |
| **Total actually paid** | | | | |

Formula: monthly cost = unit rate × usage. For hourly items, usage = 730 hours (24 × 365 / 12).

## 2. Actual cost of the project period

| Item | Hours or amount actually used | Cost |
|---|---|---|
| EC2 (from launch to termination) | | |
| RDS | | |
| S3 | | |
| Other (Elastic IP, load balancer if used) | | |
| **Total** | | |

## 3. Scaling scenario (optional, shows deeper understanding)

| Scenario | Change | Estimated monthly cost |
|---|---|---|
| Current (class demo, ~10 users) | 1 × EC2, 1 × RDS micro | |
| 500 active users | 2 × EC2 behind ALB, RDS small, ~50 GB S3 | |
| High availability | RDS Multi-AZ, EC2 in 2 Availability Zones | |

## 4. Cost-optimisation strategies used (write these up in the report)

1. **Free plan / free tier sizes**: t3.micro EC2 and micro RDS instance only.
2. **Images bypass the server**: browsers download photos straight from S3 using presigned URLs, so EC2 needs less CPU and bandwidth and a micro instance is enough.
3. **Single-AZ RDS** with storage autoscaling off for the project; Multi-AZ would only be needed in production.
4. **Upload size limit (10 MB)** and allowed file types, to control S3 storage growth.
5. **S3 lifecycle rule** to delete test uploads after 30 days.
6. **Budget alert** (zero-spend or USD 5) emailed to all members.
7. **Stopping resources** when not testing, and terminating everything after the demo.
8. **Optional add-ons (ALB, second EC2) run only during testing**, then deleted.

## Note on the AWS Free Tier

Accounts created on or after 15 July 2025 choose a credit-based **Free plan** (lasting up to 6 months or until the credits run out) or a **Paid plan**. Accounts created earlier stay on the legacy 12-month free tier. State which one your group used in the report, because it changes the "actually paid" figure.
