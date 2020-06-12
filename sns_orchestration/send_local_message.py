import boto3
import update_credentials
import os
import json
import datetime
def send(message, creds, env):
    region_name = 'us-west-2'
    topic_arns = {
        "uat":"arn:aws:sns:us-west-2:560130786230:lp-uat-sns-notification-topic",
        "prod":"arn:aws:sns:us-west-2:643705676985:lp-prod-sns-notification-topic"
    }
    topic_arn = topic_arns[env]

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

    return resp['ResponseMetadata']['HTTPStatusCode']


creds = update_credentials.assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')
message_name = "HLS.S30.T12XWS.2020116T223059.v1.5.json"
#message_name = "HLS.S30.T13WFR.2020116T181921.v1.5.json"
with open(message_name,'r') as outfile:
    message = json.load(outfile)

json_object = json.dumps(message)

outcome = send(json_object,creds,'prod')
time = datetime.datetime.utcnow()
print(message_name, " - Success at ",time) if outcome == 200 else print(message_name, "Failure at ",time)

