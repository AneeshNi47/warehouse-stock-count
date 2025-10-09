import boto3
import os
from flask import current_app

# Initialize S3 client using environment variables
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)


def upload_to_s3(file_obj, filename):
    """Uploads file to S3 (private) and returns the S3 key (not URL)."""
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError("S3_BUCKET_NAME is not configured")

    s3.upload_fileobj(
        file_obj,
        bucket,
        filename,
        ExtraArgs={"ACL": "private"}  # ❌ No public access
    )
    return filename  # store the key in DB (e.g. uploads/<filename>)


def generate_presigned_url(filename, expires_in=3600):
    """Generate a temporary download URL for private S3 files."""
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError("S3_BUCKET_NAME is not configured")

    try:
        url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": filename},
            ExpiresIn=expires_in  # expires in 1 hour
        )
        return url
    except Exception as e:
        current_app.logger.error(f"Failed to generate presigned URL: {e}")
        return None


def delete_from_s3(filename):
    """Deletes a file from S3 bucket."""
    bucket = os.environ.get("S3_BUCKET_NAME")
    if not bucket:
        raise ValueError("S3_BUCKET_NAME is not configured")

    try:
        s3.delete_object(Bucket=bucket, Key=filename)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete from S3: {e}")
        return False