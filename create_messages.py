import json
import boto3
import send_messages
import uuid
import update_credentials
import logging
import os
import hashlib

from botocore.exceptions import ClientError
from collections import OrderedDict

def compute_checksum(bucket_name, key):
    filename = "tempfile"
    creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
    client = boto3.client('s3',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    client.download_file(bucket_name,key,filename)
    with open(filename, "rb") as f:
        checksum_val = hashlib.sha512(f.read()).hexdigest()
    os.remove(filename)
    return checksum_val

#get hdf files
bucket_name = 'hls-global'
count = 0
product_id = 'S30'
folder = 'data'
data_day = "2020117"
env = "prod"
path = "/".join([product_id,folder,data_day])
header_extension = '.hdf.hdr'
FILE_TYPE = {
        "tif":'data',
        "xml":'metadata',
        "jpg":'browse'
        }
creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
S3 = boto3.resource('s3',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
        )
bucket = S3.Bucket(bucket_name)
granule_name_old = None

for obj in bucket.objects.filter(Prefix=path):
    granule_name_new = obj.key.split("/")[3]
    if granule_name_new != granule_name_old:
        granule_name_old = granule_name_new
        print(granule_name_new)
        count += 1
        creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
        S3 = boto3.resource('s3',
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken']
                )
        message = OrderedDict()
        message['collection'] = "".join(granule_name_new.split('.')[0:2])
        message['identifier'] = str(uuid.uuid1())
        message['version'] = granule_name_new[-3:]
        message['product'] = {}
        message['product']['files'] = []
        message['product']['name'] = granule_name_new
        message['product']['dataVersion'] = granule_name_new[-3:]
        granule_path = "/".join([path,granule_name_new,""])
        for file in bucket.objects.filter(Prefix=granule_path):
            file_name = file.key.split("/")[-1]
            if not file_name.endswith("json"):
                granule = OrderedDict()
                granule["name"] = file_name
                granule['checksumType'] = "SHA512"
                granule['checksum'] = compute_checksum(bucket_name,file.key)
                granule['size'] = file.size
                granule['type'] = FILE_TYPE[file_name.split(".")[-1]]
                granule['uri'] = "s3://" + bucket_name + '/' + file.key
            message["product"]["files"].append(granule)
        json_object = json.dumps(message)
        with open(granule_name_new + ".json","w") as f:
            json.dump(json_object,f)
        resp = send_messages.send(json_object, creds, env)
        print("{} Success".format(granule_name_new)) if resp == 200 else print("{} Failed".format(granule_name_new))
        if count ==  10:
            break
