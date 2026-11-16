import os
from google.cloud import storage

BUCKET_NAME = os.getenv(
    "GCS_BUCKET",
    "job-posting-cloud-2026-data"
)


def upload_file_to_gcs(content, destination_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_path)

    blob.upload_from_string(
        content,
        content_type="text/csv"
    )

    return f"gs://{BUCKET_NAME}/{destination_path}"


def download_file_from_gcs(source_path):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(source_path)

    return blob.download_as_bytes()
