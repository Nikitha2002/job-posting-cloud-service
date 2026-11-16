from app.database import get_connection
from app.processor import process_csv
from app.storage import download_file_from_gcs


def _process_batch(job_id, batch_id, storage_path, start_row):
    if not isinstance(start_row, int) or start_row < 2:
        raise ValueError("Invalid starting row")

    content = download_file_from_gcs(storage_path)
    records = process_csv(content)

    for record in records:
        record["source_row"] += start_row - 2

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id
                FROM processing_jobs
                WHERE id = %s
                FOR UPDATE
                """,
                (job_id,)
            )

            if cursor.fetchone() is None:
                raise ValueError("Job not registered")

            cursor.execute(
                """
                SELECT status
                FROM batches
                WHERE id = %s AND job_id = %s
                FOR UPDATE
                """,
                (batch_id, job_id)
            )

            batch = cursor.fetchone()
            if batch is None:
                raise ValueError("Batch not registered")

            if batch[0] == "completed":
                return {
                    "batch_id": batch_id,
                    "status": "already_completed"
                }

            cursor.execute(
                """
                UPDATE batches
                SET status = 'processing',
                    completed_at = NULL
                WHERE id = %s
                """,
                (batch_id,)
            )

            cursor.execute(
                """
                UPDATE processing_jobs
                SET status = 'processing',
                    completed_at = NULL
                WHERE id = %s
                  AND status <> 'completed'
                """,
                (job_id,)
            )

            for record in records:
                cursor.execute(
                    """
                    INSERT INTO job_postings
                        (job_id, batch_id, source_row,
                         title, location, description)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, source_row)
                    DO UPDATE SET
                        title = EXCLUDED.title,
                        location = EXCLUDED.location,
                        description = EXCLUDED.description
                    RETURNING id
                    """,
                    (
                        job_id,
                        batch_id,
                        record["source_row"],
                        record["title"],
                        record["location"],
                        record["description"]
                    )
                )

                posting_id = cursor.fetchone()[0]

                for skill in record["skills"]:
                    cursor.execute(
                        """
                        INSERT INTO job_skills
                            (posting_id, skill)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (posting_id, skill)
                    )

            cursor.execute(
                """
                UPDATE batches
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
                """,
                (batch_id,)
            )

            cursor.execute(
                """
                UPDATE processing_jobs
                SET status = 'completed',
                    completed_at = NOW()
                WHERE id = %s
                  AND NOT EXISTS (
                      SELECT 1
                      FROM batches
                      WHERE job_id = %s
                        AND status <> 'completed'
                  )
                """,
                (job_id, job_id)
            )

    return {
        "batch_id": batch_id,
        "status": "completed",
        "processed_records": len(records)
    }



def process_batch(job_id, batch_id, storage_path, start_row):
    try:
        return _process_batch(
            job_id, batch_id, storage_path, start_row
        )

    except Exception:
        import logging

        logging.exception(
            "Batch processing failed: job=%s batch=%s",
            job_id,
            batch_id
        )

        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE batches
                        SET status = 'failed'
                        WHERE id = %s
                          AND job_id = %s
                          AND status <> 'completed'
                        """,
                        (batch_id, job_id)
                    )

                    if cursor.rowcount > 0:
                        cursor.execute(
                            """
                            UPDATE processing_jobs
                            SET status = 'failed'
                            WHERE id = %s
                              AND status <> 'completed'
                            """,
                            (job_id,)
                        )

        except Exception:
            logging.exception(
                "Could not record batch failure"
            )

        raise
