import json
import sys
import time
from pathlib import Path

import requests

BASE_URL = "http://127.0.0.1:8082"
POLL_INTERVAL = 2
TIMEOUT = 300


def main():
    dataset = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "data/performance/jobs_1000.csv"
    )

    start = time.perf_counter()

    with dataset.open("rb") as file:
        response = requests.post(
            f"{BASE_URL}/upload/async",
            files={"file": (dataset.name, file, "text/csv")},
            timeout=120
        )

    api_seconds = time.perf_counter() - start
    response.raise_for_status()

    job = response.json()
    job_id = job["job_id"]

    print("Job ID:", job_id)
    print("API response time:", round(api_seconds, 3), "seconds")
    print("Total records:", job["total_records"])
    print("Total batches:", job["total_batches"])

    deadline = time.monotonic() + TIMEOUT

    while time.monotonic() < deadline:
        status_response = requests.get(
            f"{BASE_URL}/jobs/{job_id}",
            timeout=30
        )
        status_response.raise_for_status()
        status = status_response.json()

        if status["status"] == "completed":
            total_seconds = time.perf_counter() - start
            throughput = status["completed_records"] / total_seconds

            result = {
                "dataset": str(dataset),
                "job_id": job_id,
                "records": status["completed_records"],
                "batches": status["total_batches"],
                "api_seconds": round(api_seconds, 3),
                "total_seconds": round(total_seconds, 3),
                "throughput_records_per_second": round(throughput, 2),
                "status": "completed"
            }

            print(json.dumps(result, indent=2))

            output = Path("data/performance/results.jsonl")
            with output.open("a") as file:
                file.write(json.dumps(result) + "\n")

            return

        if status["status"] == "failed":
            raise RuntimeError(f"Job failed: {job_id}")

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Job did not complete within {TIMEOUT}s: {job_id}")


if __name__ == "__main__":
    main()
