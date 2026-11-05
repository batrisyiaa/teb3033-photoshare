# Team Handover: Who Owns What

The full system is already built and tested locally. Each member now **owns** one part: you will understand it, run it, finish the cloud work for it, and explain it in the report and the video. Read your section, run the app locally (see README), and ask in the group chat if anything is unclear.

Assessment note: the video needs every member to present, and the lecturer may ask questions. Make sure you can explain your own files without notes.

---

## Member 1: Frontend (React)

**Your files:** `frontend/src/` (all pages in `pages/`, `api.js`, `AuthContext.jsx`, `styles.css`)

**Understand these points:**
- `api.js` is the only place that calls the backend. It adds the `Authorization: Bearer <token>` header.
- After login, the token is saved in `localStorage`, and `App.jsx` blocks private pages when no user is logged in.
- `Feed.jsx` sends search/filter values as query parameters to `GET /api/photos`.
- `PhotoDetail.jsx` refreshes every 10 seconds so users see each other's new comments.

**Your tasks:**
1. Run the frontend locally and click through every page.
2. Improve the look if you want (colours, logo, layout). Do not change the API calls without telling Member 2.
3. Take screenshots of each page for the report.

**Report:** the presentation tier part of Section 3 (Components Used) and UI screenshots.

---

## Member 2: Backend (Flask)

**Your files:** `backend/app/` (`routes/`, `utils.py`, `storage.py`, `__init__.py`, `config.py`), `backend/tests/`, `docs/API.md`

**Understand these points:**
- Each file in `routes/` is one group of endpoints (auth, groups, photos, comments, health).
- `utils.require_member` is the permission check used before any photo or comment action.
- `storage.py` switches between local files and S3 using the `STORAGE_BACKEND` setting.
- Duplicate usernames are blocked by the database constraint, and the `IntegrityError` becomes a 409 response.

**Your tasks:**
1. Run `python -m pytest -v` in `backend/` and confirm 5 tests pass.
2. Keep `docs/API.md` up to date and share it with Member 1.
3. Help Member 4 with the `.env` values during deployment.

**Report:** Components Used (backend), the Data Flow Description, and Section 5 (Search and Filter).

---

## Member 3: Database and S3

**Your files:** `backend/app/models.py`, `backend/database/schema.sql`, the ERD and storage strategy in `docs/ARCHITECTURE.md`

**Understand these points:**
- The five tables, their primary keys, foreign keys and unique constraints.
- Why images go to S3 and only the key goes to the database.
- Why the bucket is private and uses presigned URLs.

**Your tasks:**
1. Create the RDS PostgreSQL instance and S3 bucket (Steps 1, 2 and 4 in `deploy/DEPLOYMENT.md`).
2. Run `schema.sql` on RDS and screenshot the tables (`\dt` in psql, or a pgAdmin/DBeaver screenshot).
3. Export the ERD from `docs/ARCHITECTURE.md` (paste the Mermaid code into mermaid.live) or redraw it in draw.io.

**Report:** Section 4 (Database Design) and the ERD.

---

## Member 4: Cloud Deployment and Testing

**Your files:** `deploy/`, `testing/`, `docs/COST_ESTIMATE.md`

**Understand these points:**
- How nginx, Gunicorn, Flask, RDS and S3 connect (diagram in `docs/ARCHITECTURE.md`).
- Why the IAM role is used instead of putting AWS keys in code.
- What each check in `concurrency_test.py` proves.

**Your tasks:**
1. Set the budget alert first, then follow `deploy/DEPLOYMENT.md` (Steps 0, 3, 5, 6) with Member 3.
2. Deploy an early version as soon as possible and share the URL.
3. Run `testing/concurrency_test.py` and Locust (see `testing/README.md`), and save screenshots and CSV files.
4. Fill in `docs/COST_ESTIMATE.md` with real rates and the real bill.
5. Shut everything down after the video is recorded.

**Report:** Section 6 (Deployment and Testing) and Section 7 (Cost).

---

## Shared tasks

| Task | Who |
|---|---|
| Introduction, Problem Statement, Conclusion | Split between all, then one person edits for consistent style |
| Architecture diagram | Member 4 (from `docs/ARCHITECTURE.md`) |
| Report formatting (Arial 11, max 8 pages, IEEE references size 8, rubric on the last page) | One editor |
| Video (max 2 minutes, everyone speaks, live demo) | All; roughly 25 seconds each |
| Source code zip without `node_modules`, `venv`, `dist`, `.env` | Member 2 |

## Working remotely

- Put the code in **one private GitHub repository** and add all four members. Everyone works from the same code, and Member 4 deploys with `git clone`.
- Never commit the `.env` file (passwords and keys). It is already in `.gitignore`.
- Use a short weekly online call (Teams or Google Meet), and keep a checklist of the tasks above in the group chat.

## Suggested video plan (2 minutes)

| Time | Speaker | Content |
|---|---|---|
| 0:00–0:25 | Member 1 | Problem and goal; register, log in, create a group |
| 0:25–0:50 | Member 2 | Upload a photo; comment, edit and delete; search and filter |
| 0:50–1:15 | Member 3 | Database design and S3 storage; show RDS tables and S3 objects |
| 1:15–2:00 | Member 4 | AWS architecture; two users commenting at the same time; test results; cost |
