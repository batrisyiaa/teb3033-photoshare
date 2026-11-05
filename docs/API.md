# REST API Contract (Member 2 ↔ Member 1)

Base path: `/api`. All request and response bodies are JSON, except photo upload (multipart form).

**Authentication.** Login and register return a JWT token. Every other endpoint (except `/api/health`) needs the header:

```
Authorization: Bearer <token>
```

**Errors.** Every error has the same shape: `{"error": "message"}` with a matching HTTP status (400 bad input, 401 not logged in, 403 not allowed, 404 not found, 409 conflict, 413 file too large).

## Auth

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{username, email, password, display_name?}` | 201 `{token, user}` |
| POST | `/auth/login` | `{username, password}` | 200 `{token, user}` |
| GET | `/auth/me` | none | 200 `user` |

Rules: username 3–50 characters (letters, numbers, `_`, `.`), password at least 6 characters. Duplicate username or email returns 409.

## Friend groups

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/groups` | none | 200 list of my groups |
| POST | `/groups` | `{name, description?}` | 201 group (creator becomes owner) |
| GET | `/groups/<id>` | none | 200 group with `members` (members only) |
| POST | `/groups/<id>/members` | `{username}` | 201 (any member can add a friend) |
| DELETE | `/groups/<id>/members/<user_id>` | none | 200 (owner removes anyone; member can leave) |

## Photos

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/photos` | multipart: `photo` (file), `group_id`, `caption?`, `tags?` ("beach, trip") | 201 photo |
| GET | `/photos` | query parameters below | 200 `{items, page, per_page, total, pages}` |
| GET | `/photos/<id>` | none | 200 photo with `comments` |
| DELETE | `/photos/<id>` | none | 200 (uploader or group owner) |

Allowed files: jpg, jpeg, png, gif, webp, maximum 10 MB.

**Search and filter (bonus)** on `GET /photos`. All are optional and can be combined:

| Parameter | Example | Meaning |
|---|---|---|
| `q` | `sunset` | Keyword in caption, tags, uploader name **or comment text** |
| `group_id` | `3` | Only this group |
| `uploader` | `aiman` | Uploader username |
| `tag` | `beach` | Exact tag |
| `date_from`, `date_to` | `2026-11-01` | Upload date range (inclusive) |
| `sort` | `oldest` | Default `newest` |
| `page`, `per_page` | `1`, `12` | Pagination (max 50 per page) |

Users only ever see photos from groups they belong to.

## Comments

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/photos/<id>/comments` | none | 200 list |
| POST | `/photos/<id>/comments` | `{content}` | 201 comment |
| PUT | `/comments/<id>` | `{content}` | 200 (author only; sets `edited: true`) |
| DELETE | `/comments/<id>` | none | 200 (author or photo uploader) |

## Health

`GET /health` → `{status, database, storage, server}`. The `server` field shows which machine answered, which helps prove load balancing if two servers are used.

## Example objects

```json
// photo
{
  "id": 1,
  "url": "https://bucket.s3.ap-southeast-1.amazonaws.com/photos/3/9f1c...jpg?X-Amz-...",
  "caption": "Sunset at the beach",
  "tags": ["beach", "sunset"],
  "uploader": {"id": 1, "username": "batrisyia", "display_name": "Batrisyia"},
  "group": {"id": 3, "name": "DPC Squad"},
  "comment_count": 3,
  "created_at": "2026-11-05T12:47:00+00:00"
}

// comment
{
  "id": 7, "photo_id": 1,
  "user": {"id": 2, "username": "aiman", "display_name": "Aiman"},
  "content": "Wow, the colours are amazing!",
  "created_at": "2026-11-05T12:48:10+00:00",
  "updated_at": null, "edited": false
}
```
