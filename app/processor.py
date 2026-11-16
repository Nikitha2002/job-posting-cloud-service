import csv
import io
import re

REQUIRED_COLUMNS = {"title", "location", "description"}

TECHNICAL_SKILLS = {
    "Python": r"\bpython\b",
    "SQL": r"\bsql\b",
    "AWS": r"\baws\b",
    "GCP": r"\bgcp\b|\bgoogle cloud\b",
    "Azure": r"\bazure\b",
    "Tableau": r"\btableau\b",
    "Power BI": r"\bpower\s*bi\b",
    "Spark": r"\bspark\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
}

def extract_skills(description):
    text = description or ""
    return sorted(
        skill
        for skill, pattern in TECHNICAL_SKILLS.items()
        if re.search(pattern, text, re.IGNORECASE)
    )

def process_csv(content):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("CSV must use UTF-8 encoding")

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV is empty or missing headers")

    reader.fieldnames = [
        name.strip().lower() for name in reader.fieldnames
    ]

    if not REQUIRED_COLUMNS.issubset(reader.fieldnames):
        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        raise ValueError(
            f"Missing required columns: {', '.join(sorted(missing))}"
        )

    records = []

    for row_number, row in enumerate(reader, start=2):
        title = (row.get("title") or "").strip()
        location = (row.get("location") or "").strip()
        description = (row.get("description") or "").strip()

        if not title or not description:
            continue

        records.append({
            "title": " ".join(title.split()),
            "location": " ".join(location.split()),
            "description": description,
            "skills": extract_skills(description),
            "source_row": row_number,
        })

    return records
