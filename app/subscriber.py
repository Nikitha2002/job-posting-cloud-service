import json
import os

from google.cloud import pubsub_v1
from app.worker import process_batch

PROJECT_ID = os.getenv("GCP_PROJECT", "job-posting-cloud-2026")
SUBSCRIPTION_ID = os.getenv(
    "PUBSUB_SUBSCRIPTION",
    "job-processing-worker-sub"
)


def main():
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        PROJECT_ID,
        SUBSCRIPTION_ID
    )

    def callback(message):
        try:
            task = json.loads(message.data.decode("utf-8"))

            result = process_batch(
                job_id=task["job_id"],
                batch_id=task["batch_id"],
                storage_path=task["storage_path"],
                start_row=task["start_row"]
            )

            print("Processed:", result, flush=True)
            message.ack()

        except Exception as error:
            print("Processing failed:", error, flush=True)
            message.nack()

    streaming_pull = subscriber.subscribe(
        subscription_path,
        callback=callback
    )

    print("Worker listening for messages...", flush=True)

    try:
        streaming_pull.result()
    except KeyboardInterrupt:
        streaming_pull.cancel()
    finally:
        subscriber.close()


if __name__ == "__main__":
    main()
