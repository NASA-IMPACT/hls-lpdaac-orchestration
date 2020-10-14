import boto3
import datetime
import gzip
import json
import pandas as pd

def retrieve_inventory(bucket, manifest_key):
    manifest = json.load(s3.Object(bucket, manifest_key).get()['Body'])
    appended_data = []
    for obj in manifest['files']:
        gzip_obj = s3.Object(bucket_name=bucket, key=obj['key'])
        buffer = gzip.open(gzip_obj.get()["Body"], mode='rt')
        data = pd.read_csv(buffer, names = ["Bucket", "Object", "Size", "Last_Modified"],sep=",")
        appended_data.append(data)

    inventory = pd.concat(appended_data)
    inventory["Last_Modified"] = pd.to_datetime(inventory.Last_Modified,infer_datetime_format=True,utc=True)

    return inventory

def filter_inventory(inventory, start_date, end_date):
    inventory = inventory.set_index("Object")
    print(f"Searching for files created or modified between {start_date} and {end_date}")
    filtered_objects = inventory.filter(regex="^(S30|L30)\/data\/.*(tif|jpg|xml)$", axis=0)
    day_filter = (filtered_objects["Last_Modified"].ge(start_date) & filtered_objects["Last_Modified"].lt(end_date))
    final_objects = filtered_objects[day_filter]
    print(final_objects["Last_Modified"].min(), final_objects["Last_Modified"].max())
    final_objects = extract_checksum(final_objects)
    create_rec_report(final_objects,start_date)

def extract_checksum(final_objects):
    print("starting checksum: ", datetime.datetime.now())
    client = boto3.client("s3")
    checksums = []
    print(len(final_objects.index))
    for key in final_objects.index:
        bucket = final_objects.loc[key,:]["Bucket"]
        metadata = client.head_object(Bucket=bucket, Key=key)
        checksums.append(metadata["ETag"].replace('"',""))
    final_objects["Checksum"] = checksums
    print("finished checksum: ", datetime.datetime.now())
    return final_objects

def create_rec_report(report,date):
    report_date = date.strftime("%Y%j")
    file_name = f"HLS_reconcile_{report_date}.rpt"
    del report["Bucket"]

    report = report.rename(index=lambda s: s.split("/")[-1])
    report["Short_Name"] = ["".join(x.split(".")[0:2]) for x in report.index]
    report["Version"] = [".".join(x.split(".")[4:6])[1:] for x in report.index]
    report = report.reset_index()
    report = report.reindex(columns = ["Short_Name", "Version", "Object", "Size", "Last_Modified","Checksum"])
    report.to_csv(path_or_buf=file_name,sep=",",date_format="%Y-%m-%dT%H:%M:%SZ",header=False,index=False,mode="w")
    upload_to_s3(file_name, report_date)

def upload_to_s3(report_name,report_date):
    client = boto3.client("s3")
    client.upload_file(report_name,bucket,f"reconciliation_reports/{report_date}/{report_name}")

if __name__ == "__main__":
    print(datetime.datetime.now())
    s3 = boto3.resource("s3")
    end_date = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    end_date = end_date.replace(hour=0,minute=0,second=0,microsecond=0)
    start_date = end_date - datetime.timedelta(days=1)
    date_path = end_date.strftime("%Y-%m-%dT00-00Z")
    bucket = "hls-global"
    manifest_key = f"reconciliation_reports/hls-global/HLS_data_products/{date_path}/manifest.json"
    inventory = retrieve_inventory(bucket, manifest_key)
    start_date = pd.to_datetime(start_date).tz_localize("UTC")
    end_date = pd.to_datetime(end_date).tz_localize("UTC")
    filter_inventory(inventory,start_date, end_date)

