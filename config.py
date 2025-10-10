import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "devkey")

    database_url = os.environ.get("DATABASE_URL")

    # Heroku uses old-style 'postgres://' URLs — fix it for SQLAlchemy
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or "sqlite:///stockcount.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AWS / S3
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")