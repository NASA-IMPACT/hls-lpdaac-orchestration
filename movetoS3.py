import boto3
import update_credentials
import logging
import os
import hashlib

from botocore.exceptions import ClientError

def move_to_S3(old_bucket, new_bucket, old_key, new_key):
    creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
    client = boto3.client('s3',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    try:
        response = client.copy_object(CopySource={"Bucket":old_bucket, "Key":old_key},Bucket=new_bucket,Key=new_key)
    except ClientError as e:
        logging.error(e)
        return False
    return True

#get hdf files
bucket_name = "hls-testing-sentinel-output"
path = "HLS.S30.T06KTF.2020045T200849.v1.5"
S3 = boto3.resource('s3')
bucket = S3.Bucket(bucket_name)
new_bucket = 'hls-global'
base_path = "S30/{}/"
for obj in bucket.objects.filter(Prefix=path):
    file_name = obj.key.split('/')[-1]
    if file_name.endswith('tif'):
        object_path = base_path.format('data')  + file_name
    elif file_name.endswith('xml'):
        object_path = base_path.format('metadata') + file_name
    elif file_name.endswith('jpg'):
        object_path = base_path.format('thumbnail') + file_name
    else:
        continue
    result = move_to_S3(bucket_name,new_bucket,obj.key, object_path)
    print(object_path)
    print(result)
