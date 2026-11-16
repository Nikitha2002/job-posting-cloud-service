import csv
import io
import uuid


def split_csv_into_batches(content, batch_size=1000, job_id=None):
    if job_id is None:
        job_id = str(uuid.uuid4())
    if batch_size < 1:
        raise ValueError("Batch size must be positive")

    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise ValueError("CSV is missing headers")

    fieldnames = reader.fieldnames
    rows = list(reader)

    if not rows:
        raise ValueError("CSV contains no records")

    batches = []

    for start in range(0, len(rows), batch_size):
        batch_rows = rows[start:start + batch_size]

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(batch_rows)

        batch_number = len(batches) + 1
        batch_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{job_id}:{batch_number}"))

        batches.append({
            "job_id": job_id,
            "batch_id": batch_id,
            "batch_number": len(batches) + 1,
            "start_row": start + 2,
            "record_count": len(batch_rows),
            "content": output.getvalue().encode("utf-8")
        })

    return batches
