from app.batch_processor import split_csv_into_batches
from app.storage import upload_file_to_gcs
from app.messaging import publish_batch_task
from app.job_tracking import register_distributed_job


def distribute_csv_batches(content, job_id, batch_size=1000, filename='uploaded.csv'):
    batches = split_csv_into_batches(
        content,
        batch_size=batch_size,
        job_id=job_id
    )

    register_distributed_job(filename, batches)

    results = []

    for batch in batches:
        storage_path = (
            f"batches/{job_id}/{batch['batch_id']}.csv"
        )

        storage_uri = upload_file_to_gcs(
            batch["content"],
            storage_path
        )

        message = publish_batch_task(
            job_id=job_id,
            batch_id=batch["batch_id"],
            storage_path=storage_path,
            start_row=batch["start_row"]
        )

        results.append({
            "batch_id": batch["batch_id"],
            "batch_number": batch["batch_number"],
            "record_count": batch["record_count"],
            "start_row": batch["start_row"],
            "storage_uri": storage_uri,
            "message_id": message["message_id"]
        })

    return results
