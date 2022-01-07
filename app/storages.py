import boto3

from server.settings.base import env


def get_s3_connection():
    return boto3.client(
        's3',
        aws_access_key_id=env('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=env('AWS_SECRET_ACCESS_KEY'),
        region_name=env('REGION_NAME'),
    )


def s3_upload_image(image_file, resource_url):
    s3 = get_s3_connection()
    s3.upload_fileobj(
        image_file,
        env('S3_BUCKET_NAME'),
        resource_url,
        ExtraArgs={
            "ContentType": image_file.content_type,
        }
    )

def s3_delete_image(image):
    s3 = get_s3_connection()
    s3.Object(env('S3_BUCKET_NAME'), image.url).delete()