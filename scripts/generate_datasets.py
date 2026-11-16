import csv
from pathlib import Path

OUTPUT_DIR = Path("data/performance")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROLES = [
    "Data Analyst",
    "Data Scientist",
    "Data Engineer"
]

LOCATIONS = [
    "Boulder CO",
    "Denver CO",
    "Remote"
]

DESCRIPTIONS = [
    "Python SQL Tableau Power BI",
    "Python TensorFlow PyTorch AWS",
    "Python SQL Spark Docker Kubernetes GCP"
]


def generate_dataset(size):
    output = OUTPUT_DIR / f"jobs_{size}.csv"

    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["title", "location", "description"])

        for index in range(size):
            category = index % len(ROLES)

            writer.writerow([
                ROLES[category],
                LOCATIONS[category],
                DESCRIPTIONS[category]
            ])

    print(f"Created {output}: {size} records")


if __name__ == "__main__":
    for size in (1000, 2000, 5000, 10000):
        generate_dataset(size)
