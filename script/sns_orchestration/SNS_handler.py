import json
import boto3


def assume_role(role_arn,role_session_name):
    client = boto3.client('sts')
    creds = client.assume_role(RoleArn=role_arn, RoleSessionName=role_session_name)
    return creds['Credentials']

def send(message, creds):
    region_name = 'us-west-2'
    topic_arn = "arn:aws:sns:us-west-2:611670965994:HLS-data-notification"

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

with open("sample_success_message.json") as f:
    message = json.load(f)

creds = assume_role('arn:aws:iam::611670965994:role/gcc-S3Test','brian_test')

status = message["response"]["status"].upper()

if status == "FAILURE":
    print("sending email")
    result = send(json.dumps(message),creds)
    print(result)
