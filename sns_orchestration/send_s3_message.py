import boto3
import update_credentials
import os
import json
import datetime

def send(message, creds, message_name):
    region_name = 'us-west-2'
    topic_arns = {
        "uat":"arn:aws:sns:us-west-2:560130786230:lp-uat-sns-notification-topic",
        "prod":"arn:aws:sns:us-west-2:643705676985:lp-prod-sns-notification-topic"
    }
    topic_arn = topic_arns["uat"]

    aws_access_key_id = creds.get('AccessKeyId')
    aws_secret_access_key = creds.get('SecretAccessKey')
    aws_session_token = creds.get('SessionToken')

    client = boto3.client('sns', aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          aws_session_token=aws_session_token,
                          region_name=region_name)
    resp = client.publish(
        TopicArn=topic_arn,
        Message=message
    )
    outcome = resp['ResponseMetadata']['HTTPStatusCode']
    time = datetime.datetime.utcnow()
    print(message_name, " - Success at ",time) if outcome == 200 else print(message_name, "Failure at ",time)

def get_message_from_s3(creds, bucket_name, path):
    S3 = boto3.resource("s3",
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretAccessKey'],
            aws_session_token=creds['SessionToken']
            )
    bucket = S3.Bucket(bucket_name)
    count = 0
    for obj in bucket.objects.filter(Prefix=path):
        if obj.key.endswith("v1.5.json"):
            count += 1
            file = obj.get()
            message = file['Body'].read().decode()
            print(obj.key)
            print(json.loads(message)["identifier"])
            #send(message, creds, obj.key)
    return count

#get hdf files
bucket_name = 'hls-global'
product_id = 'S30'
folder = 'data'
date = "2020116"
failed_granules = [
        "T16XDR",
        "T15XWL",
        "T17XNL",
        "T18XWR",
        "T20XNS",
        "T23XNM",
        "T22XDR",
        "T23XNL",
        "T19XEL",
        "T24XVR",
        ]

successful_granules = [
        "T04VEL",
        "T05KPA",
        "T01KAS",
        "T01KBB",
        "T01KBT",
        "T01WFN",
        "T03VUJ",
        "T03VVJ",
        "T03VWH",
        "T03WVM",
        ]
granules = failed_granules
total_messages = 0
for granule in granules:
    path = "/".join([product_id,folder,date,f"HLS.S30.{granule}"])
    creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
    total_messages += get_message_from_s3(creds, bucket_name, path)

print("Total messages sent: ", total_messages)

