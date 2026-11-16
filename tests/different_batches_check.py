import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.batch_processor import split_csv_into_batches
from app.job_tracking import register_distributed_job
from app.storage import upload_file_to_gcs
from app.worker import process_batch
from app.database import get_connection


def main():
    job_id = str(uuid.uuid4())
    content = Path("data/sample_jobs.csv").read_bytes()

    batches = split_csv_into_batches(
        content,
        batch_size=2,
        job_id=job_id
    )

    register_distributed_job("different_batches_test.csv", batches)

    tasks = []
    for batch in batches:
        path = f"batches/{job_id}/{batch['batch_id']}.csv"
        upload_file_to_gcs(batch["content"], path)
        tasks.append((batch, path))

    def run_worker(task):
        batch, path = task
        return process_batch(
            job_id=job_id,
            batch_id=batch["batch_id"],
            storage_path=path,
            start_row=batch["start_row"]
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(run_worker, tasks))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM processing_jobs WHERE id = %s",
                (job_id,)
            )
            job_status = cursor.fetchone()[0]

            cursor.execute(
                "SELECT status FROM batches WHERE job_id = %s",
                (job_id,)
            )
            batch_statuses = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                "SELECT COUNT(*) FROM job_postings WHERE job_id = %s",
                (job_id,)
            )
            record_count = cursor.fetchone()[0]

    print("Job ID:", job_id)
    print("Worker results:", results)
    print("Job status:", job_status)
    print("Batch statuses:", batch_statuses)
    print("Saved records:", record_count)

    assert job_status == "completed"
    assert all(status == "completed" for status in batch_statuses)
    assert record_count == 3

    print("Different-batch concurrency test PASSED")


if __name__ == "__main__":
    main()
