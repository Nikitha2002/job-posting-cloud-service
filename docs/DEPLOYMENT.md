# Google Cloud Deployment Guide

## Project

Cloud-Based Job Posting Processing and Analytics Service

Participant: Nikitha Lalam

This guide documents the Google Cloud resources and configuration
used for the final project deployment.

## 1. Prerequisites

Install and configure:

- Google Cloud CLI
- Python 3.12
- Docker-compatible build environment
- PostgreSQL client tools

A Google Cloud project with billing enabled is required.

## 2. Configure Google Cloud

Set the project and region:

    export PROJECT_ID=job-posting-cloud-2026
    export REGION=us-central1

    gcloud config set project "$PROJECT_ID"

Enable required APIs:

    gcloud services enable \
      run.googleapis.com \
      cloudbuild.googleapis.com \
      artifactregistry.googleapis.com \
      sqladmin.googleapis.com \
      storage.googleapis.com \
      pubsub.googleapis.com \
      secretmanager.googleapis.com \
      iam.googleapis.com

Replace the project ID when deploying in another environment.

## 3. Required Resources

Create or provision:

- Artifact Registry Docker repository: job-posting-repo
- Cloud Storage bucket: job-posting-cloud-2026-data
- Cloud SQL PostgreSQL instance: job-posting-postgres
- PostgreSQL database: job_postings_db
- PostgreSQL user: job_posting_app
- Pub/Sub topic: job-processing-tasks
- Secret Manager secret: job-posting-db-password

Use the SQL statements in scripts/schema.sql to initialize
the application database.

## 4. Service Accounts

Create three service accounts:

- job-posting-api-sa
- job-posting-worker-sa
- job-posting-push-sa

Assign the following permissions.

API service account:

- roles/cloudsql.client
- roles/storage.objectCreator on the data bucket
- roles/pubsub.publisher on the processing topic
- roles/secretmanager.secretAccessor on the database secret

Worker service account:

- roles/cloudsql.client
- roles/storage.objectViewer on the data bucket
- roles/secretmanager.secretAccessor on the database secret

Pub/Sub push service account:

- roles/run.invoker on the worker Cloud Run service

Pub/Sub's service agent must also have permission to mint
authentication tokens for the push service account.

## 5. Build API Container

    gcloud builds submit \
      --tag us-central1-docker.pkg.dev/job-posting-cloud-2026/job-posting-repo/job-posting-api:v3 \
      --project=job-posting-cloud-2026

## 6. Build Worker Container

    gcloud builds submit \
      --config=cloudbuild-worker-v4.yaml \
      --project=job-posting-cloud-2026

The Cloud Build configuration contains project-specific image names.
Update these names for another Google Cloud project.

## 7. Deploy Cloud Run Services

Deploy the API and worker using their respective Docker images.

Both services require:

- Cloud SQL instance attachment
- INSTANCE_CONNECTION_NAME
- DB_NAME
- DB_USER
- DB_PASSWORD from Secret Manager
- Appropriate service accounts

The API also requires access to Cloud Storage and Pub/Sub.

The worker must remain private.

The original deployment used:

- Region: us-central1
- Memory: 512 MiB
- CPU: 1
- Maximum instances: 2
- Container concurrency: 2

## 8. Configure Pub/Sub Push

Create an authenticated push subscription from
job-processing-tasks to:

    https://WORKER_SERVICE_URL/pubsub/push

Use job-posting-push-sa for OIDC authentication.

Configure:

- Acknowledgment deadline: 60 seconds
- Minimum retry delay: 10 seconds
- Maximum retry delay: 600 seconds
- Maximum delivery attempts: 5
- Dead-letter topic for failed messages

Grant the Pub/Sub service agent the required dead-letter
publishing and subscription permissions.

## 9. Verify Deployment

Start an authenticated API proxy:

    gcloud run services proxy job-posting-api \
      --region=us-central1 \
      --project=job-posting-cloud-2026 \
      --port=8082

In another terminal:

    curl http://127.0.0.1:8082/health

Submit a sample CSV:

    curl -X POST \
      http://127.0.0.1:8082/upload/async \
      -F "file=@data/sample_jobs.csv;type=text/csv"

Use the returned job ID to check processing status:

    curl http://127.0.0.1:8082/jobs/JOB_ID

## 10. Run Tests

    python -m pytest tests/ -q

Generate benchmark datasets:

    python scripts/generate_datasets.py

Run a benchmark:

    python scripts/benchmark.py data/performance/jobs_5000.csv

## 11. Security and Limitations

- Do not commit passwords or service-account keys.
- Use Secret Manager for database credentials.
- Keep the worker private.
- Grant minimum necessary IAM permissions.
- Cloud SQL and other resources may incur charges.
- Resource names must be updated for another project.
- This guide documents the original deployment and is not
  an automated infrastructure provisioning script.
