import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection():
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(
            database_url,
            cursor_factory=RealDictCursor
        )

    return psycopg2.connect(
        host="localhost",
        database="railway_db",
        user="example_user",
        password="example_password",
        port="5432",
        cursor_factory=RealDictCursor
    )