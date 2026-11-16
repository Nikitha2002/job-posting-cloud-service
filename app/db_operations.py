import uuid

from app.database import get_connection


def save_job_postings(filename, records):
    job_id = str(uuid.uuid4())
    batch_id = str(uuid.uuid4())

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO processing_jobs
                    (id, filename, status, total_records)
                VALUES (%s, %s, 'processing', %s)
                """,
                (job_id, filename, len(records))
            )

            cursor.execute(
                """
                INSERT INTO batches
                    (id, job_id, status, record_count)
                VALUES (%s, %s, 'processing', %s)
                """,
                (batch_id, job_id, len(records))
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
                        INSERT INTO job_skills (posting_id, skill)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (posting_id, skill)
                    )

            cursor.execute(
                """
                UPDATE batches
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
                """,
                (batch_id,)
            )

            cursor.execute(
                """
                UPDATE processing_jobs
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
                """,
                (job_id,)
            )

    return {
        "job_id": job_id,
        "batch_id": batch_id,
        "saved_records": len(records),
        "status": "completed"
    }
