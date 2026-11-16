import pytest

from app.processor import process_csv, extract_skills


def test_extract_skills():
    description = "Experience with Python, SQL and Tableau"
    assert extract_skills(description) == [
        "Python", "SQL", "Tableau"
    ]


def test_valid_csv():
    content = (
        b"title,location,description\n"
        b"Data Analyst,Boulder,Python and SQL required\n"
    )

    records = process_csv(content)

    assert len(records) == 1
    assert records[0]["title"] == "Data Analyst"
    assert records[0]["skills"] == ["Python", "SQL"]


def test_missing_columns():
    content = b"title,location\nData Analyst,Boulder\n"

    with pytest.raises(ValueError, match="Missing required columns"):
        process_csv(content)


def test_empty_csv():
    with pytest.raises(ValueError, match="empty"):
        process_csv(b"")


def test_invalid_encoding():
    with pytest.raises(ValueError, match="UTF-8"):
        process_csv(b"\xff\xfe\xfa")


def test_skip_incomplete_records():
    content = (
        b"title,location,description\n"
        b",Boulder,Python required\n"
        b"Data Engineer,Denver,SQL required\n"
    )

    records = process_csv(content)

    assert len(records) == 1
    assert records[0]["title"] == "Data Engineer"
