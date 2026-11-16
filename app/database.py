import os
import psycopg


def get_connection():
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(database_url)

    instance_connection_name = os.getenv(
        "INSTANCE_CONNECTION_NAME"
    )

    if instance_connection_name:
        return psycopg.connect(
            dbname=os.getenv("DB_NAME", "job_postings_db"),
            user=os.getenv("DB_USER", "job_posting_app"),
            password=os.environ["DB_PASSWORD"],
            host=f"/cloudsql/{instance_connection_name}",
            connect_timeout=10
        )

    return psycopg.connect(
        "dbname=job_postings_db user=nila6795"
    )
