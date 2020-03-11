import json
import boto3
import os
import csv
import glob
import update_credentials
from botocore.exceptions import ClientError

def initiate_client(creds,service):
    client = boto3.client(service,
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    return client
def initiate_resource(creds,service):
    resource = boto3.resource(service,
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    return resource
def retrieve_message(obj):
    file = obj.get()
    message = json.loads(file['Body'].read().decode())
    date = obj.key.split('-')[-3]
    report_name = write_report(message,date)
    return report_name

def write_report(message, date):
    report_name = OUTPUT_FILE_NAME.format(date)
    writer = 'w' if not os.path.exists(report_name) else 'a'
    with open(report_name,writer) as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',')
        shortname = message['collection']
        version = message['version']
        for file in message['product']['files']:
            filename = file['name']
            size = file['size']
            obj = RESOURCE.ObjectSummary(BUCKET_NAME,file['uri'].split('hls-global/')[-1])
            modified = obj.last_modified.strftime("%Y-%m-%dT%H:%M:%SZ")
            checksum = file['checksum']
            spamwriter.writerow([shortname,version,filename,size,modified,checksum])        
    return report_name
def move_to_S3(bucket_name,report_name):
    object_name = "/".join(['reconciliation_reports',report_name.split('.rpt')[0].split('_')[-1],report_name])
    creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
    client = boto3.client('s3',
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    try:
        response = client.upload_file(report_name,bucket_name,object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

msg_location = "messages/"
OUTPUT_FILE_NAME = "HLS_reconcile_{}.rpt"
BUCKET_NAME = 'hls-global'
role = 'arn:aws:iam::611670965994:role/gcc-S3Test'
session = 'reports'
creds = update_credentials.assume_role(role,session)
RESOURCE = initiate_resource(creds,'s3')
CLIENT = initiate_client(creds,'s3')
bucket = RESOURCE.Bucket(BUCKET_NAME)

for obj in bucket.objects.filter(Prefix=msg_location):
    report_name = None if obj.key == "messages/" else retrieve_message(obj)

print("Successfully generated report: ", report_name) if move_to_S3(BUCKET_NAME,report_name) is True else print("Failed to generate report: ", report_name)
