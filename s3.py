import boto3
import os
import dynamo

def s3_client():
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    return s3_client
    
def upload_to_s3(object_name, file_name):
    s3_client = s3_client()
    S3_BUCKET = os.getenv("S3_BUCKET")
    response = s3_client.upload_file(filename=file_name, bucket=S3_BUCKET, key=object_name)