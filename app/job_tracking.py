import uuid

from app.database import get_connection


def register_distributed_job(filename, batches):
    if not batches:
        raise ValueError("At least one batch is required")

    job_ids = {str(batch["job_id"]) for batch in batches}

    if len(job_ids) != 1:
        raise ValueError("All batches must belong to the same job")

    job_id = next(iter(job_ids))
    uuid.UUID(job_id)

    total_records = sum(batch["record_count"] for batch in batches)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO processing_jobs
                    (id, filename, status, total_records)
                VALUES (%s, %s, 'pending', %s)
                """,
                (job_id, filename, total_records)
            )

            for batch in batches:
                cursor.execute(
                    """
                    INSERT INTO batches
                        (id, job_id, status, record_count)
                    VALUES (%s, %s, 'pending', %s)
                    """,
                    (
                        batch["batch_id"],
                        job_id,
                        batch["record_count"]
                    )
                )

    return {
        "job_id": job_id,
        "status": "pending",
        "total_records": total_records,
        "total_batches": len(batches)
    }


def get_job_status(job_id):
    uuid.UUID(str(job_id))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, filename, status, total_records,
                       completed_at
                FROM processing_jobs
                WHERE id = %s
                """,
                (str(job_id),)
            )

            job = cursor.fetchone()

            if job is None:
                return None

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_batches,
                    COUNT(*) FILTER (
                        WHERE status = 'completed'
                    ) AS completed_batches,
                    COALESCE(
                        SUM(record_count) FILTER (
                            WHERE status = 'completed'
                        ), 0
                    ) AS completed_records
                FROM batches
                WHERE job_id = %s
                """,
                (str(job_id),)
            )

            total_batches, completed_batches, completed_records = (
                cursor.fetchone()
            )

    progress = (
        round(completed_batches / total_batches * 100, 2)
        if total_batches else 0
    )

    return {
        "job_id": str(job[0]),
        "filename": job[1],
        "status": job[2],
        "total_records": job[3],
        "completed_records": completed_records,
        "total_batches": total_batches,
        "completed_batches": completed_batches,
        "progress_percent": progress,
        "completed_at": (
            job[4].isoformat() if job[4] else None
        )
    }
