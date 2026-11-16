from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "running" in response.json()["message"]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_upload(monkeypatch):
    monkeypatch.setattr(
        "app.main.upload_file_to_gcs",
        lambda content, destination: "gs://test-bucket/test.csv"
    )
    monkeypatch.setattr(
        'app.main.save_job_postings',
        lambda filename, records: {
            'job_id': 'test-job-id',
            'status': 'completed'
        }
    )
    content = (
        b"title,location,description\n"
        b"Data Analyst,Boulder,Python and SQL required\n"
    )

    response = client.post(
        "/upload",
        files={"file": ("jobs.csv", content, "text/csv")}
    )

    assert response.status_code == 200
    assert response.json()["total_records"] == 1
    assert response.json()["records"][0]["skills"] == [
        "Python", "SQL"
    ]


def test_invalid_file_type():
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")}
    )

    assert response.status_code == 400
    assert "Only CSV" in response.json()["detail"]


def test_missing_csv_columns():
    content = b"name,city\nAnalyst,Boulder\n"

    response = client.post(
        "/upload",
        files={"file": ("jobs.csv", content, "text/csv")}
    )

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]
