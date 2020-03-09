import json
import boto3
import send_messages
import uuid
import update_credentials
import logging
import os

from botocore.exceptions import ClientError
from collections import OrderedDict

def write_message(bucket_name,file_name):
    product_id = file_name.split('.')[1]
    message = OrderedDict()
    message['collection'] = "".join(file_name.split('.')[0:2])
    message['identifier'] = str(uuid.uuid1())
    message['version'] = file_name[-3:]
    message['product'] = {}
    message['product']['files'] = [{},{},{}]
    message['product']['name'] = file_name
    message['product']['dataVersion'] = file_name[-3:]
    for i,file in enumerate(message['product']['files']):
        file['name'] = file_name + FILE_EXTENSIONS[i]
        key = "/".join([product_id,FILE_TYPE[i],file['name']])
        key = key.replace('browse','thumbnail') if FILE_TYPE[i] is 'browse' else key
        obj = S3.ObjectSummary(bucket_name, key)
        file['checksum-type'] = "MD5"
        file['checksum'] = obj.e_tag.replace("\"","")
        file['size'] = obj.size
        file['type'] = FILE_TYPE[i]
        file['uri'] = "s3://" + bucket_name + '/' + obj.key
    message_name = 'hls-cnm-notification-message-' + file_name.replace('.','-') + '.json'
    with open(message_name,'w') as outfile:
         json.dump(message,outfile)
    json_object = json.dumps(message)
    return json_object, message_name

def move_to_S3(bucket_name,message_name):
    object_name = "/".join(['messages',message_name.split('-')[-3],message_name])
    creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
    client = boto3.client('s3',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    try:
        response = client.upload_file(message_name,bucket_name,object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

#get hdf files
bucket_name = 'hls-global'
count = 0
product_id = 'S30'
folder = 'data'
path = "/".join([product_id,folder,''])
header_extension = '.hdf.hdr'
FILE_EXTENSIONS = ['.hdf','.cmr.xml','.jpeg']
FILE_TYPE = ['data','metadata','browse']
creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
S3 = boto3.resource('s3',
        aws_access_key_id=creds['AccessKeyId'],
        aws_secret_access_key=creds['SecretAccessKey'],
        aws_session_token=creds['SessionToken']
        )
bucket = S3.Bucket(bucket_name)

for obj in bucket.objects.filter(Prefix=path):
    file_name = obj.key.split('/')[-1]
    if file_name.endswith('hdr'):
        count += 1
        json_object, message_name = write_message(bucket_name,file_name.replace(header_extension,''))
        resp = send_messages.send(json_object, creds)
        result = move_to_S3(bucket_name,message_name) if resp == 200 else False
        print("{} Success".format(message_name)) if result is True else print("{} Failed".format(message_name))
        os.remove(message_name) if result is True else None
    if count ==  8:
        break
