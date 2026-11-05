# PhotoShare: Distributed Photo-Sharing and Commenting System

TEB3033 Distributed and Parallel Computing, group project.

A multi-tier web application where friends create groups, upload photos to their group, and comment on each other's photos, with search and filter (bonus).

| Tier | Technology |
|---|---|
| Presentation | React 18 (Vite), served by nginx |
| Application | Python Flask REST API, Gunicorn, JWT authentication |
| Data | PostgreSQL (Amazon RDS) |
| Storage | Amazon S3 (private bucket, presigned URLs) |
| Cloud | AWS EC2, RDS, S3, IAM (region ap-southeast-1) |

## Folder structure

```
photoshare/
├── backend/            Flask API (application tier)
│   ├── app/            models, routes, storage, config
│   ├── database/       schema.sql (PostgreSQL)
│   ├── tests/          automated API tests (pytest)
│   └── .env.example    settings template
├── frontend/           React app (presentation tier)
├── deploy/             AWS deployment guide, nginx, systemd, setup scripts
├── testing/            concurrency test and Locust load test
└── docs/               API contract, architecture + ERD, cost template, team handover
```

## Run locally (no AWS needed)

Requirements: Python 3.10+ and Node.js 18+.

**Terminal 1: backend**

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate     Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # Mac/Linux: cp .env.example .env
python wsgi.py                       # API on http://localhost:5000
```

Locally it uses SQLite and saves photos in `backend/uploads/`, so nothing needs to be installed or paid for.

**Terminal 2: frontend**

```bash
cd frontend
npm install
npm run dev                          # open http://localhost:5173
```

Register two or three accounts (use a private browser window for the second user), create a group, add the others by username, then upload and comment.

**Run the tests**

```bash
cd backend
python -m pytest -v
```

## Deploy to AWS

See [`deploy/DEPLOYMENT.md`](deploy/DEPLOYMENT.md).

## Documentation

- [`docs/TEAM_HANDOVER.md`](docs/TEAM_HANDOVER.md): who owns which part, and the tasks left for each member
- [`docs/API.md`](docs/API.md): REST API contract
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): architecture diagram, data flow, ERD, concurrency design
- [`docs/COST_ESTIMATE.md`](docs/COST_ESTIMATE.md): cost table template and optimisation strategies
- [`testing/README.md`](testing/README.md): how to run the multi-user tests
