from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

VALID_ID = "11111111-2222-4333-8444-555555555555"


def test_completed_job(monkeypatch):
    def fake_get_job_status(job_id):
        return {
            "job_id": job_id,
            "filename": "sample_jobs.csv",
            "status": "completed",
            "total_records": 3,
            "completed_records": 3,
            "total_batches": 1,
            "completed_batches": 1,
            "progress_percent": 100.0,
            "completed_at": None
        }

    monkeypatch.setattr(
        "app.main.get_job_status",
        fake_get_job_status
    )

    response = client.get(f"/jobs/{VALID_ID}")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["progress_percent"] == 100.0


def test_invalid_job_id():
    response = client.get("/jobs/not-a-valid-uuid")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid job ID"


def test_nonexistent_job(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_job_status",
        lambda job_id: None
    )

    response = client.get(f"/jobs/{VALID_ID}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
