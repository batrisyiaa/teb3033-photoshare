-- PhotoShare database schema (PostgreSQL 15+)
-- Data tier. The Flask app also creates these tables automatically on first
-- start (db.create_all), but this script documents the design and can be run
-- by hand:  psql "$DATABASE_URL" -f schema.sql

CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    email          VARCHAR(120) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,          -- hashed, never plain text
    display_name   VARCHAR(100),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS friend_groups (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  VARCHAR(255),
    owner_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Many-to-many link between users and friend groups.
CREATE TABLE IF NOT EXISTS group_members (
    id         SERIAL PRIMARY KEY,
    group_id   INTEGER NOT NULL REFERENCES friend_groups(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'member')),
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_group_user UNIQUE (group_id, user_id)
);

-- Photo metadata only. The image file itself lives in S3 at storage_key.
CREATE TABLE IF NOT EXISTS photos (
    id                 SERIAL PRIMARY KEY,
    uploader_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id           INTEGER NOT NULL REFERENCES friend_groups(id) ON DELETE CASCADE,
    storage_key        VARCHAR(255) NOT NULL UNIQUE,   -- e.g. photos/3/9f1c....jpg
    original_filename  VARCHAR(255),
    content_type       VARCHAR(50),
    caption            TEXT,
    tags               VARCHAR(500) DEFAULT '',        -- lowercase, comma-separated
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS comments (
    id          SERIAL PRIMARY KEY,
    photo_id    INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ                          -- set when a comment is edited
);

-- Indexes for the feed and search/filter queries.
CREATE INDEX IF NOT EXISTS ix_group_members_user  ON group_members(user_id);
CREATE INDEX IF NOT EXISTS ix_photos_group        ON photos(group_id);
CREATE INDEX IF NOT EXISTS ix_photos_uploader     ON photos(uploader_id);
CREATE INDEX IF NOT EXISTS ix_photos_created      ON photos(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_comments_photo      ON comments(photo_id);
