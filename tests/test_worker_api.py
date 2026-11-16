import base64
import json

from fastapi.testclient import TestClient
from app.worker_api import app

client = TestClient(app)


def test_worker_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_pubsub_push(monkeypatch):
    def fake_process_batch(job_id, batch_id, storage_path, start_row):
        return {
            "batch_id": batch_id,
            "status": "completed",
            "processed_records": 3
        }

    monkeypatch.setattr(
        "app.worker_api.process_batch",
        fake_process_batch
    )

    task = {
        "job_id": "test-job",
        "batch_id": "test-batch",
        "storage_path": "batches/test.csv",
        "start_row": 2
    }

    encoded = base64.b64encode(
        json.dumps(task).encode("utf-8")
    ).decode("utf-8")

    response = client.post(
        "/pubsub/push",
        json={"message": {"data": encoded}}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["processed_records"] == 3


def test_invalid_pubsub_push():
    response = client.post(
        "/pubsub/push",
        json={"message": {"data": "not-valid-base64!"}}
    )

    assert response.status_code == 400


def test_processing_failure_returns_http_500(monkeypatch):
    def fake_process_batch(**kwargs):
        raise RuntimeError("Simulated processing failure")

    monkeypatch.setattr(
        "app.worker_api.process_batch",
        fake_process_batch
    )

    task = {
        "job_id": "test-job",
        "batch_id": "test-batch",
        "storage_path": "batches/test.csv",
        "start_row": 2
    }

    encoded = base64.b64encode(
        json.dumps(task).encode("utf-8")
    ).decode("utf-8")

    test_client = TestClient(
        app,
        raise_server_exceptions=False
    )

    response = test_client.post(
        "/pubsub/push",
        json={"message": {"data": encoded}}
    )

    assert response.status_code == 500
