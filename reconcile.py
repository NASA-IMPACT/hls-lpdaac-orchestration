import json
import boto3
import os
import csv
import datetime
from botocore.exceptions import ClientError

def assume_role(role_arn,role_session_name):
    client = boto3.client('sts')
    creds = client.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
    return creds['Credentials']

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

def get_datetime(year=None,month=None,day=None,offset=1):
    if year is None or month is None or day is None:
        print("Missing year, day, or month. Processing for now minus the offset value")
        now = datetime.datetime.utcnow() - datetime.timedelta(days=offset)
    else:
        now = datetime.datetime(year,month,day)
    
    return now

def retrieve_message(obj):
    file = obj.get()
    message = json.loads(file['Body'].read().decode())
    report_name = write_report(message)
    return report_name

def write_report(message):
    report_name = OUTPUT_FILE_NAME.format(DATE)
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
    print(report_name)
    object_name = "/".join([PROD,'reconciliation_reports',report_name.split('.rpt')[0].split('_')[-1],report_name])
    creds = assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
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

print("Started: ", datetime.datetime.utcnow())
OUTPUT_FILE_NAME = "HLS_reconcile_{}.rpt"
BUCKET_NAME = 'hls-global'
role = 'arn:aws:iam::611670965994:role/gcc-S3Test'
session = 'reports'
creds = assume_role(role,session)
RESOURCE = initiate_resource(creds,'s3')
CLIENT = initiate_client(creds,'s3')
processed_date = get_datetime().date()
DATE = f"{processed_date.timetuple().tm_year}{processed_date.timetuple().tm_yday:03}"
PROD = "S30"
msg_location = "/".join([PROD,"data"])

bucket = RESOURCE.Bucket(BUCKET_NAME)
count = 0
report_name = None
for obj in bucket.objects.filter(Prefix=msg_location):
    if obj.key.endswith("v1.5.json") and obj.last_modified.date() == processed_date:
        count +=1
        report_name = retrieve_message(obj)

print(f"Number of granules processed for {processed_date.strftime('%Y%m%d')}: {count}")

if report_name is not None:
    print("Successfully generated report: ", report_name) if move_to_S3(BUCKET_NAME,report_name) is True else print("Failed to generate report: ", report_name)
else:
    print("No data was produced for date " + processed_date.strftime("%Y%m%d"))
print("Finished: ", datetime.datetime.utcnow())
