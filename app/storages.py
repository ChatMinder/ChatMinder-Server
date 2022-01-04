import boto3

from server.settings.base import env


def get_s3_connection():
    return boto3.client(
        's3',
        aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'),
        region_name=env('REGION_NAME'),
    )
