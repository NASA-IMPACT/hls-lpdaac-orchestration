import boto3
import os

def send(message, creds):
    region_name = 'us-west-2'
    topic_arn = 'arn:aws:sns:us-west-2:560130786230:lp-uat-sns-notification-topic'

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
