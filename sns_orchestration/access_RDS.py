import boto3
import datetime
import json
from collections import OrderedDict

def get_cf_resources(stackname):
    cloudformation = boto3.resource("cloudformation")
    stack = cloudformation.Stack(stackname)
    resources = stack.resource_summaries.all()
    secret = None
    for resource in list(resources):
        if "RdsRdsSecret" in resource.logical_id:
            secret = resource.physical_resource_id
    return secret

def create_arn(rdsname):
    region = boto3.session.Session().region_name
    account = boto3.client("sts").get_caller_identity().get("Account")
    prefix = "arn:aws:rds"
    arn = ":".join([prefix,region,account,"cluster",rdsname])
    return arn

def rds_statement(rdsname, arn, secret, sql, sql_parameters):
    rds_client = boto3.client("rds-data")
    response = rds_client.execute_statement(
        secretArn=secret,
        database="hls",
        resourceArn=arn,
        sql=sql,
        parameters=sql_parameters,
    )
    print(response["records"])
    return response

def process_response(response):
    output = []
    for record in response["records"][0]:
        value = record.get("stringValue")
        if value is not None : output.append(value)
    return output

def hls_filename(input_granule):
        granule_components = input_granule.split("_")
        tt = datetime.datetime.strptime(granule_components[2],"%Y%m%dT%H%M%S").timetuple()
        date = f"{tt.tm_year}{tt.tm_yday}"
        hhmmss = f"{tt.tm_hour}{tt.tm_min}{tt.tm_sec}"
        hls_granule = ".".join(["HLS","S30",granule_components[5],date,hhmmss,"v1.5"])
        return hls_granule

def create_report(identifier,output):
    report = OrderedDict()
    report["identifier"] = identifier
    report["granules"] = []
    for input_granule in output:
        granule = OrderedDict()
        granule["input_granule"] = input_granule
        granule["hls_granule"] = hls_filename(input_granule)
        report["granules"].append(granule)
    report["error_message"] = "<insert message from LP here>"
    return report

stackname = "hls-harkins-ebs"
rdsname = "-".join(["rds",stackname])
secret = get_cf_resources(stackname)
print(secret)
arn = create_arn(rdsname)
identifier = "3d601b9c-c4a1-48fd-8cb8-9edc5e340bd6"
identifier = "3d601b9c-c4a1-48fd-8cb8-9edc5e340bd6"
sql = "SELECT granule FROM granule_log WHERE event ->> 'JobId' = :identifier;"
sql_parameters = [{"name": "identifier", "value": {"stringValue": identifier}}]
response = rds_statement(rdsname,arn,secret,sql, sql_parameters)
output = process_response(response)
report = create_report(identifier,output)
report["stackname"] = stackname

with open("new_report.json","w") as f:
    json.dump(report,f)
print(report)
