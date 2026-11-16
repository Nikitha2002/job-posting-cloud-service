# Cloud-Based Job Posting Processing and Analytics Service

**Course:** CSCI 4253/5253 - Datacenter Scale Computing
**Project participant:** Nikitha Lalam
**Project type:** Individual Final Project

## Overview

This project implements a cloud-based service for asynchronous processing and analysis of job-posting CSV datasets.

Users submit a CSV file through a FastAPI endpoint. The service divides the file into batches, stores the batches in Google Cloud Storage, and publishes processing tasks to Google Cloud Pub/Sub.

Authenticated Cloud Run workers process the batches and store cleaned job postings and extracted technical skills in Cloud SQL for PostgreSQL.

REST endpoints allow users to retrieve processing progress and analytics results.

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| REST API | Python, FastAPI, Uvicorn | CSV uploads, job tracking and analytics |
| Object storage | Google Cloud Storage | Store CSV batches |
| Message queue | Google Cloud Pub/Sub | Distribute asynchronous processing tasks |
| Compute | Docker, Google Cloud Run | Host API and worker services |
| Database | Cloud SQL for PostgreSQL | Persist postings, skills and processing status |
| Testing | pytest, FastAPI TestClient | Automated application testing |
| Monitoring | Google Cloud Logging | Inspect worker requests and failures |

## System Architecture

```text
Client
  |
  | POST /upload/async
  v
FastAPI - Cloud Run API
  |
  +--> Cloud SQL: Register job and batches
  |
  +--> Cloud Storage: Upload batch CSV files
  |
  +--> Pub/Sub: Publish batch messages
                    |
                    | Authenticated push
                    v
             Cloud Run Worker
                    |
                    +--> Download CSV from Cloud Storage
                    +--> Validate and process records
                    +--> Extract technical skills
                    +--> Store results in Cloud SQL
                    +--> Update batch and job status

Client
  |
  +--> GET /jobs/{job_id}
  +--> GET /analytics/skills
  +--> GET /analytics/roles
  +--> GET /analytics/locations
```

## Required CSV Format

The input CSV must contain these columns:

- `title`
- `location`
- `description`

Example:

```csv
title,location,description
Data Analyst,Boulder CO,Python SQL Tableau
Data Scientist,Denver CO,Python TensorFlow AWS
Data Engineer,Remote,Python SQL Spark Docker
```

Skill extraction uses predefined regular-expression patterns rather than a trained machine-learning model.

## Local Setup

Requirements:

- Python 3.12
- PostgreSQL
- Google Cloud CLI
- A Google Cloud project with the required services enabled

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For local PostgreSQL development, configure a valid `DATABASE_URL`.

For Google Cloud deployment, configure Cloud SQL connectivity and the database credentials through environment variables and Secret Manager.

## Environment Variables

| Variable | Purpose |
|---|---|
| `GCP_PROJECT` | Google Cloud project ID |
| `GCS_BUCKET` | Cloud Storage bucket |
| `PUBSUB_TOPIC` | Pub/Sub processing topic |
| `DATABASE_URL` | Optional PostgreSQL connection URL |
| `INSTANCE_CONNECTION_NAME` | Cloud SQL instance connection name |
| `DB_NAME` | PostgreSQL database name |
| `DB_USER` | PostgreSQL application user |
| `DB_PASSWORD` | Database password, supplied securely |

Do not commit credentials or `.env` files.

## Database Initialization

The PostgreSQL schema is defined in:

```text
scripts/schema.sql
```

Initialize the target database with:

```bash
psql "$DATABASE_URL" -f scripts/schema.sql
```

The database contains four main tables:

- `processing_jobs`
- `batches`
- `job_postings`
- `job_skills`

Database constraints and transaction-aware writes help prevent duplicate processing during message redelivery.

## Running the API Locally

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

Run the worker API separately:

```bash
uvicorn app.worker_api:app --host 127.0.0.1 --port 8081
```

The API requires accessible PostgreSQL and Google Cloud services for operations that use those dependencies.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Application information |
| GET | `/health` | API health |
| POST | `/upload` | Synchronous CSV processing |
| POST | `/upload/async` | Asynchronous batch submission |
| GET | `/jobs/{job_id}` | Processing status and progress |
| GET | `/analytics/skills` | Technical skill frequencies |
| GET | `/analytics/roles` | Job counts by role |
| GET | `/analytics/locations` | Job counts by location |

Worker endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Worker health |
| GET | `/health/db` | Cloud SQL connectivity check |
| POST | `/pubsub/push` | Pub/Sub push message processing |

## Example Asynchronous Upload

```bash
curl -X POST \
  http://127.0.0.1:8080/upload/async \
  -F "file=@data/sample_jobs.csv;type=text/csv"
```

The response contains a job ID, batch metadata, and the initial processing status.

Check progress:

```bash
curl http://127.0.0.1:8080/jobs/JOB_ID
```

Query analytics:

```bash
curl http://127.0.0.1:8080/analytics/skills
curl http://127.0.0.1:8080/analytics/roles
curl http://127.0.0.1:8080/analytics/locations
```

## Cloud Deployment

The application uses separate Docker images for the API and worker.

API image:

```bash
gcloud builds submit \
  --tag REGION-docker.pkg.dev/PROJECT_ID/REPOSITORY/job-posting-api:TAG \
  --project=PROJECT_ID
```

Worker image:

```bash
gcloud builds submit \
  --config=cloudbuild-worker-v4.yaml \
  --project=job-posting-cloud-2026
```

The worker Cloud Build configuration uses the deployment-specific image path from this project. Replace it with your own project and repository when deploying elsewhere.

Both services require appropriate IAM permissions, Cloud SQL connectivity, and database credentials.

The worker is deployed privately. An authenticated Pub/Sub push subscription invokes `/pubsub/push`.

The Pub/Sub subscription uses retry backoff and a dead-letter topic for repeatedly failing messages.

## Automated Testing

Run the complete test suite:

```bash
python -m pytest tests/ -q
```

Latest result:

```text
22 passed
```

Additional concurrency test scripts:

```bash
python -m tests.concurrency_check
python -m tests.different_batches_check
```

These integration scripts require working database and Cloud Storage credentials.

## Performance Evaluation

Synthetic CSV datasets were generated with known job titles, locations and technical skills.

| Records | Batches | Total time (seconds) | Throughput (records/sec) |
|---|---:|---:|---:|
| 1,000 | 1 | 25.905 | 38.60 |
| 2,000 | 2 | 33.604 | 59.52 |
| 5,000 | 5 | 71.493 | 69.94 |
| 10,000 | 10 | 178.132 | 56.14 |

The 10,000-record workload completed successfully, with all 10 batches and 10,000 records verified in PostgreSQL.

### Worker Configuration Comparison

Both experiments used the same 5,000-record dataset and container concurrency of 1.

| Maximum instances | Completion time | Throughput |
|---|---:|---:|
| 1 | 73.816 seconds | 67.74 records/sec |
| 2 | 76.001 seconds | 65.79 records/sec |

Increasing the maximum permitted instances did not improve completion time in this single-run comparison.

Actual simultaneous instance counts were not independently verified.

## Reliability

The service uses:

- Stable batch identifiers
- PostgreSQL uniqueness constraints
- Transaction-aware processing
- Duplicate completed-batch detection
- Failure-state tracking
- Retry-state transitions
- Pub/Sub redelivery
- Dead-letter forwarding

An isolated Pub/Sub experiment demonstrated five rejected delivery attempts followed by successful dead-letter forwarding.

Automated tests cover simulated processing failures, retry-state handling and HTTP 500 responses.

## Known Limitations

- Technical skill extraction uses a fixed vocabulary.
- The system does not currently provide salary analytics.
- Performance results are based on limited benchmark runs.
- Worker scaling benefits were not conclusively established.
- The batch submission process is not fully atomic across storage, database registration and message publishing.
- Live recovery of a valid failed batch has not yet been demonstrated end-to-end.

## Project Deliverables

- Source code and automated tests
- Deployment configuration
- Database schema
- Benchmark script
- Performance and reliability evaluation
- Written final project report
- Presentation and demonstration video

## Author

Nikitha Lalam
University of Colorado Boulder
MS in Data Science

## Reproducing Benchmark Datasets

The benchmark datasets are generated synthetically using fixed job roles,
locations, and technical skill descriptions.

Generate all four datasets:

    python scripts/generate_datasets.py

This creates CSV files containing 1,000, 2,000, 5,000, and 10,000
job-posting records in `data/performance/`.

The generated datasets are excluded from Git because they can be
recreated using the generator.

To run a benchmark, first start an authenticated proxy to the deployed
Cloud Run API on port 8082:

    gcloud run services proxy job-posting-api \
      --region=us-central1 \
      --project=job-posting-cloud-2026 \
      --port=8082

In a separate terminal, run:

    python scripts/benchmark.py data/performance/jobs_5000.csv

The benchmark measures API response time, end-to-end processing time,
throughput, and final job status.

Measured results are preserved in `data/performance/results.jsonl`.

Results can vary due to Cloud Run cold starts, instance scaling,
database performance, and other cloud infrastructure conditions.

## Google Cloud Deployment Prerequisites

The application was deployed in Google Cloud using the following resources:

| Resource | Name |
|---|---|
| Google Cloud project | `job-posting-cloud-2026` |
| Region | `us-central1` |
| Artifact Registry repository | `job-posting-repo` |
| Cloud Storage bucket | `job-posting-cloud-2026-data` |
| Cloud SQL instance | `job-posting-postgres` |
| PostgreSQL database | `job_postings_db` |
| PostgreSQL application user | `job_posting_app` |
| Pub/Sub topic | `job-processing-tasks` |
| Cloud Run API | `job-posting-api` |
| Cloud Run worker | `job-posting-worker` |
| Secret Manager secret | `job-posting-db-password` |

### Required Google Cloud APIs

Enable the following services:

- Cloud Run API
- Cloud Build API
- Artifact Registry API
- Cloud SQL Admin API
- Cloud Storage API
- Pub/Sub API
- Secret Manager API
- IAM API

### Service Accounts

The deployment uses three service accounts:

- `job-posting-api-sa`: Runs the FastAPI application.
- `job-posting-worker-sa`: Runs the batch-processing worker.
- `job-posting-push-sa`: Authenticates Pub/Sub push requests.

### Required IAM Permissions

The API service account requires access to:

- Cloud Storage objects
- Pub/Sub topic publishing
- Cloud SQL connections
- Secret Manager database credentials

The worker service account requires access to:

- Cloud Storage objects
- Cloud SQL connections
- Secret Manager database credentials

The Pub/Sub push service account requires permission to invoke
the private Cloud Run worker.

Use least-privilege IAM permissions rather than granting project-wide
Owner or Editor access.

### Database Configuration

Initialize the PostgreSQL database using `scripts/schema.sql`.

The schema defines processing jobs, batches, job postings, technical
skills, uniqueness constraints, and query indexes.

### Environment Configuration

Set the following variables when deploying the application:

- `INSTANCE_CONNECTION_NAME`
- `DB_NAME`
- `DB_USER`
- `GCP_PROJECT`
- `GCS_BUCKET`
- `PUBSUB_TOPIC`

Supply `DB_PASSWORD` through Secret Manager rather than committing
the password to source control.

### Deployment Notes

The API and worker are separate Cloud Run services.

The worker is private and accepts authenticated Pub/Sub push requests
at `/pubsub/push`.

The deployed processing subscription uses retry backoff and a
dead-letter topic.

The resource names above describe the original deployment.
Users deploying into another Google Cloud project must replace
project-specific names and configure their own IAM permissions.

## Detailed Deployment Guide

See [Google Cloud Deployment Guide](docs/DEPLOYMENT.md) for
cloud prerequisites, service-account permissions, container builds,
Cloud Run deployment, Pub/Sub configuration, and verification steps.
