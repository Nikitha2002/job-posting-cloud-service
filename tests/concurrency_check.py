import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.batch_processor import split_csv_into_batches
from app.job_tracking import register_distributed_job
from app.storage import upload_file_to_gcs
from app.worker import process_batch


def main():
    job_id = str(uuid.uuid4())
    content = Path("data/sample_jobs.csv").read_bytes()

    batches = split_csv_into_batches(
        content,
        batch_size=10,
        job_id=job_id
    )

    register_distributed_job("concurrency_test.csv", batches)

    batch = batches[0]
    storage_path = f"batches/{job_id}/{batch['batch_id']}.csv"

    upload_file_to_gcs(batch["content"], storage_path)

    def run_worker():
        return process_batch(
            job_id=job_id,
            batch_id=batch["batch_id"],
            storage_path=storage_path,
            start_row=batch["start_row"]
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_worker) for _ in range(2)]
        results = [future.result() for future in futures]

    print("Job ID:", job_id)
    print("Worker results:", results)

    from app.database import get_connection

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM job_postings WHERE job_id = %s",
                (job_id,)
            )
            count = cursor.fetchone()[0]

    print("Saved postings:", count)
    print("No duplicates:", count == 3)


if __name__ == "__main__":
    main()
