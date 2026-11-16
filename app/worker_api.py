import base64
import binascii
import json

from fastapi import FastAPI, HTTPException, Request

from app.worker import process_batch

app = FastAPI(
    title="Job Posting Batch Worker",
    version="1.0.0"
)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    try:
        envelope = await request.json()
        encoded = envelope["message"]["data"]
        task = json.loads(
            base64.b64decode(encoded, validate=True).decode("utf-8")
        )

        required = ("job_id", "batch_id", "storage_path", "start_row")
        if not isinstance(task, dict) or any(key not in task for key in required):
            raise ValueError("Missing required task fields")

        if not isinstance(task["start_row"], int) or task["start_row"] < 2:
            raise ValueError("Invalid starting row")

    except (KeyError, TypeError, ValueError, json.JSONDecodeError,
            UnicodeDecodeError, binascii.Error):
        raise HTTPException(
            status_code=400,
            detail="Invalid Pub/Sub message"
        )

    result = process_batch(
        job_id=task["job_id"],
        batch_id=task["batch_id"],
        storage_path=task["storage_path"],
        start_row=task["start_row"]
    )

    return result


@app.get("/health/db")
def database_health():
    from app.database import get_connection

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()[0]

        return {
            "database": "connected",
            "query_result": result
        }

    except Exception:
        import logging
        logging.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )
