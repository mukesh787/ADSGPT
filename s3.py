import boto3
import os
import dynamo
from botocore.exceptions import ClientError, WaiterError

def s3_client():
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    return s3_client
    
def upload_to_s3(object_name, file_obj):
    client = s3_client()
    S3_BUCKET = os.getenv("S3_BUCKET")
    mimetype = 'image/jpeg'
    try:
        response = client.upload_fileobj(file_obj, S3_BUCKET, object_name, ExtraArgs={"ContentType": mimetype})
    except ClientError as e:
        return None
    
    response = "https://{0}.s3.ap-south-1.amazonaws.com/{1}".format(S3_BUCKET, object_name)
    return response