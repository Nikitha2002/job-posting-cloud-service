import json
import os

from google.cloud import pubsub_v1

PROJECT_ID = os.getenv(
    "GCP_PROJECT",
    "job-posting-cloud-2026"
)

TOPIC_ID = os.getenv(
    "PUBSUB_TOPIC",
    "job-processing-tasks"
)


def publish_batch_task(job_id, batch_id, storage_path, start_row=None):
    publisher = pubsub_v1.PublisherClient()

    topic_path = publisher.topic_path(
        PROJECT_ID,
        TOPIC_ID
    )

    message = {
        "job_id": job_id,
        "batch_id": batch_id,
        "storage_path": storage_path,
        "start_row": start_row
    }

    data = json.dumps(message).encode("utf-8")

    future = publisher.publish(topic_path, data)
    message_id = future.result(timeout=30)

    return {
        "message_id": message_id,
        "message": message
    }
