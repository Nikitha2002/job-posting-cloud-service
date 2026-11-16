from app.database import get_connection


def get_top_skills(limit=10):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT skill, COUNT(*) AS count
                FROM job_skills
                GROUP BY skill
                ORDER BY count DESC, skill ASC
                LIMIT %s
                """,
                (limit,)
            )
            return [
                {"skill": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]


def get_jobs_by_role():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT title, COUNT(*) AS count
                FROM job_postings
                GROUP BY title
                ORDER BY count DESC, title ASC
                """
            )
            return [
                {"title": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]


def get_jobs_by_location():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT location, COUNT(*) AS count
                FROM job_postings
                GROUP BY location
                ORDER BY count DESC, location ASC
                """
            )
            return [
                {"location": row[0], "count": row[1]}
                for row in cursor.fetchall()
            ]
