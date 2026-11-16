import pytest
from unittest.mock import MagicMock

from app import worker


def make_mock_connection(rowcount=1):
    connection = MagicMock()
    connection.__enter__.return_value = connection

    cursor = MagicMock()
    cursor.rowcount = rowcount

    connection.cursor.return_value.__enter__.return_value = cursor

    return connection, cursor


def test_failure_marks_batch_and_job_failed(monkeypatch):
    connection, cursor = make_mock_connection(rowcount=1)

    monkeypatch.setattr(
        worker,
        "_process_batch",
        MagicMock(side_effect=RuntimeError("Simulated failure"))
    )

    monkeypatch.setattr(
        worker,
        "get_connection",
        MagicMock(return_value=connection)
    )

    with pytest.raises(RuntimeError, match="Simulated failure"):
        worker.process_batch(
            "test-job", "test-batch", "test.csv", 2
        )

    assert cursor.execute.call_count == 2


def test_completed_batch_is_not_marked_failed(monkeypatch):
    connection, cursor = make_mock_connection(rowcount=0)

    monkeypatch.setattr(
        worker,
        "_process_batch",
        MagicMock(side_effect=RuntimeError("Duplicate failure"))
    )

    monkeypatch.setattr(
        worker,
        "get_connection",
        MagicMock(return_value=connection)
    )

    with pytest.raises(RuntimeError, match="Duplicate failure"):
        worker.process_batch(
            "test-job", "test-batch", "test.csv", 2
        )

    assert cursor.execute.call_count == 1


def test_failure_status_update_error_is_reraised(monkeypatch):
    connection, cursor = make_mock_connection()
    cursor.execute.side_effect = RuntimeError("Database unavailable")

    monkeypatch.setattr(
        worker,
        "_process_batch",
        MagicMock(side_effect=ValueError("Processing failed"))
    )

    monkeypatch.setattr(
        worker,
        "get_connection",
        MagicMock(return_value=connection)
    )

    with pytest.raises(ValueError, match="Processing failed"):
        worker.process_batch(
            "test-job", "test-batch", "test.csv", 2
        )


def test_failed_batch_can_be_retried_successfully(monkeypatch):
    connection, cursor = make_mock_connection()

    cursor.fetchone.side_effect = [
        ("test-job",),
        ("failed",),
        (123,)
    ]

    monkeypatch.setattr(
        worker,
        "download_file_from_gcs",
        lambda path: b"test csv content"
    )

    monkeypatch.setattr(
        worker,
        "process_csv",
        lambda content: [
            {
                "source_row": 2,
                "title": "Data Analyst",
                "location": "Boulder CO",
                "description": "Python SQL",
                "skills": ["Python", "SQL"]
            }
        ]
    )

    monkeypatch.setattr(
        worker,
        "get_connection",
        lambda: connection
    )

    result = worker.process_batch(
        "test-job",
        "test-batch",
        "test.csv",
        2
    )

    assert result["status"] == "completed"
    assert result["processed_records"] == 1

    statements = [
        call.args[0]
        for call in cursor.execute.call_args_list
    ]

    assert any(
        "SET status = 'processing'" in sql
        and "UPDATE batches" in sql
        for sql in statements
    )

    assert any(
        "SET status = 'processing'" in sql
        and "UPDATE processing_jobs" in sql
        for sql in statements
    )
