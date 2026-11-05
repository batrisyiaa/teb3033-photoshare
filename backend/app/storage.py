"""Photo file storage. S3 in the cloud; a local folder for development.

Both classes expose the same three methods, so the routes do not care which
one is active. Switch with STORAGE_BACKEND=s3 or STORAGE_BACKEND=local.
"""
import os

from flask import current_app, url_for


class LocalStorage:
    def __init__(self, folder):
        self.folder = folder
        os.makedirs(folder, exist_ok=True)

    def save(self, fileobj, key, content_type):
        path = os.path.join(self.folder, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fileobj.save(path)

    def url(self, key):
        return url_for("photos.serve_local_file", key=key, _external=False)

    def delete(self, key):
        path = os.path.join(self.folder, key)
        if os.path.exists(path):
            os.remove(path)


class S3Storage:
    """Private bucket. Browsers get short-lived presigned URLs, so photos are
    never public and only logged-in group members can see them."""

    def __init__(self, bucket, region, expiry):
        import boto3  # imported here so local development does not need AWS
        from botocore.config import Config

        # Credentials come from the EC2 IAM role (no keys in code).
        # Regional endpoint + SigV4 so presigned URLs work in every region.
        self.client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
        self.bucket = bucket
        self.expiry = expiry

    def save(self, fileobj, key, content_type):
        self.client.upload_fileobj(
            fileobj.stream, self.bucket, key, ExtraArgs={"ContentType": content_type}
        )

    def url(self, key):
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=self.expiry
        )

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)


def init_storage(app):
    cfg = app.config
    if cfg["STORAGE_BACKEND"] == "s3":
        if not cfg["S3_BUCKET"]:
            raise RuntimeError("STORAGE_BACKEND=s3 but S3_BUCKET is not set")
        app.extensions["storage"] = S3Storage(cfg["S3_BUCKET"], cfg["AWS_REGION"], cfg["S3_URL_EXPIRY_SECONDS"])
    else:
        app.extensions["storage"] = LocalStorage(cfg["LOCAL_UPLOAD_DIR"])


def storage():
    return current_app.extensions["storage"]
