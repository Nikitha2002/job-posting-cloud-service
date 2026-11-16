from app.storage import upload_file_to_gcs
from fastapi import FastAPI, UploadFile, File, HTTPException

from app.processor import process_csv
from app.db_operations import save_job_postings

app = FastAPI(
    title="Job Posting Processing and Analytics Service",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Job Posting Processing Service is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    content = await file.read()

    try:
        records = process_csv(content)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    import uuid
    storage_path = f"uploads/{uuid.uuid4()}.csv"
    gcs_uri = upload_file_to_gcs(content, storage_path)

    result = save_job_postings(file.filename, records)

    return {
        "filename": file.filename,
        "total_records": len(records),
        "job_id": result["job_id"],
        "storage_uri": gcs_uri,
        "status": result["status"],
        "records": records
    }


from app.analytics import (
    get_top_skills,
    get_jobs_by_role,
    get_jobs_by_location,
)


@app.get("/analytics/skills")
def analytics_skills(limit: int = 10):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )
    return {"skills": get_top_skills(limit)}


@app.get("/analytics/roles")
def analytics_roles():
    return {"roles": get_jobs_by_role()}


@app.get("/analytics/locations")
def analytics_locations():
    return {"locations": get_jobs_by_location()}


@app.post("/upload/async", status_code=202)
async def upload_csv_async(file: UploadFile = File(...)):
    import uuid
    from app.batch_distribution import distribute_csv_batches

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="CSV file is empty"
        )

    job_id = str(uuid.uuid4())

    try:
        batches = distribute_csv_batches(
            content,
            job_id=job_id,
            batch_size=1000,
            filename=file.filename
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    return {
        "job_id": job_id,
        "filename": file.filename,
        "status": "pending",
        "total_batches": len(batches),
        "total_records": sum(
            batch["record_count"] for batch in batches
        ),
        "batches": batches
    }


from app.job_tracking import get_job_status


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    try:
        result = get_job_status(job_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID"
        )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return result
