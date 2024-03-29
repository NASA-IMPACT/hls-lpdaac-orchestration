import boto3
import datetime
import gzip
import json
import os
import pandas as pd
import time


class query_inventory():

    def __init__(self):
        self.client = boto3.client("athena")
        with open("database_params.json", "r") as f:
            params = json.load(f)
        self.catalog = params["catalog"]
        self.database = params["database"]
        self.table = params["table"]
        self.output_location = params["output_location"]
        self.check_table()
        self.query_manager()

    def check_table(self):
        queryString = f"SHOW TABLES LIKE '{self.table}'"
        tables = self.query_athena(queryString)
        if len(tables["ResultSet"]["Rows"]) < 1:
            with open("table_params.txt","r") as f:
                queryString = f.read().replace("\n","")
            queryString = queryString.format(self.table)
            result = self.query_athena(queryString)
        else:
            print(" ".join([
                    f"Table {self.table} exists in {self.database}.",
                    "Retrieving the most recent partition"
                    ]
                   )
                 )

    def get_last_partition(self):
        queryString = f'SELECT * FROM "{self.table}$partitions" ORDER BY dt DESC'
        partitions = self.query_athena(queryString)
        print(len(partitions["ResultSet"]["Rows"]))
        if len(partitions["ResultSet"]["Rows"]) >= 2:
            partitionDate = partitions["ResultSet"]["Rows"][1]["Data"][0]["VarCharValue"]
        return partitionDate

    def query_athena(self, queryString):
        query = self.submit_query(queryString)
        queryId = query["QueryExecutionId"]
        state = self.get_query_state(queryId)
        while state == "QUEUED" or state == "RUNNING":
            print(f"Query state is currently {state} for Query: '{queryString}'. Waiting 15 seconds")
            time.sleep(15)
            state = self.get_query_state(queryId)

        if state == "SUCCEEDED":
            result = self.get_query_results(queryId)
            return result

        elif state == "FAILED" or state == "CANCELLED":
            print(f"Query returned as {state}. Exiting.")
        else:
            print("You should not be here. Exiting.")
        exit()

    def submit_query(self, queryString):
        response = self.client.start_query_execution(
                QueryString=queryString,
                QueryExecutionContext={
                    "Catalog": self.catalog,
                    "Database": self.database
                    },
                ResultConfiguration={
                    "OutputLocation": self.output_location
                    }
                )

        return response

    def get_query_state(self, queryId):
        response = self.client.get_query_execution(
                QueryExecutionId=queryId
                )
        self.output = response["QueryExecution"]["ResultConfiguration"]["OutputLocation"]
        state = response["QueryExecution"]["Status"]["State"]
        return state

    def get_query_results(self, queryId):
        response = self.client.get_query_results(
                QueryExecutionId=queryId
                )
        return response

    def query_manager(self):
        self.date = datetime.date.today()
        self.partitionDate = self.get_last_partition()
        partitionDate = datetime.datetime.strptime(self.partitionDate,"%Y-%m-%d-%H-%M").date()
        if self.date > partitionDate:
            queryString = f"MSCK REPAIR TABLE {self.table}"
            result = self.query_athena(queryString)
            self.partitionDate = self.get_last_partition()
        print(f"Successfully found partition for {self.partitionDate}")
        self.get_files()

    def get_files(self):
        self.start_date = self.date - datetime.timedelta(days=2)
        self.end_date = self.start_date + datetime.timedelta(days=1)
        start_date = f"{self.start_date:%Y-%m-%dT00:00:00}"
        end_date = f"{self.end_date:%Y-%m-%dT00:00:00}"
        print(f"Start Date: {start_date}, End Date: {end_date}")
        queryString = " ".join([
                f"SELECT key, size, last_modified FROM {self.table}", 
                f"WHERE dt like '{self.partitionDate}' AND",
                "date_parse(last_modified,'%Y-%m-%dT%H:%i:%s.%fZ') >=",
                f"date_parse('{start_date}', '%Y-%m-%dT%H:%i:%s') AND",
                "date_parse(last_modified,'%Y-%m-%dT%H:%i:%s.%fZ') <",
                f"date_parse('{end_date}', '%Y-%m-%dT%H:%i:%s') ORDER BY",
                "date_parse(last_modified,'%Y-%m-%dT%H:%i:%s.%fZ')"
                ]
            )
        result = self.query_athena(queryString)
        if len(result["ResultSet"]["Rows"]) < 2:
            print("The query returned a response with 0 rows. Nothing more to do. Exiting.")
            exit()
        self.read_csv()

    def read_csv(self):
        path = self.output.split("//")[-1]
        self.bucket = path.split("/")[0]
        key = "/".join(path.split("/")[1:])
        inventory = pd.read_csv(self.output,
                                names = ["key", "size", "last_modified"],
                                sep=","
                                )

        self.create_report(inventory)

    def create_report(self, inventory):
        inventory = inventory.set_index("key")
        filtered = inventory.filter(regex="^(S30|L30)\/data\/.*(tif|jpg|xml|stac.json)$", axis=0)
        report = filtered.rename(index=lambda s: s.split("/")[-1])
        report.loc[:,"short_name"] = ["".join(x.split(".")[0:2]) for x in report.index]
        report.loc[:,"version"] = [".".join(x.split(".")[4:6])[1:].strip("_stac") for x in report.index]
        report.loc[:, "checksum"] = ["NA" for x in report.index]
        report = report.reset_index()
        version = report["version"][0]
        report = report.reindex(columns = ["short_name", "version", "key", "size", "last_modified", "checksum"])
        filename = f"HLS_reconcile_{self.start_date:%Y%j}_{version}.rpt"
        report.to_csv(path_or_buf=filename, sep=",", date_format="%Y-%m-%dT%H:%M:%SZ", header=False, index=False, mode="w")
        self.upload_to_s3(filename)

    def upload_to_s3(self, report_name):
        client = boto3.client("s3")
        key = f"reconciliation_reports/{self.start_date:%Y%j}/{report_name}"
        client.upload_file(report_name, self.bucket, key)
        print(" ".join([
            f"Successfully uploaded {report_name} to",
            f"s3://{self.bucket}/{key}"
            ]
            )
            )
        os.remove(report_name)


if __name__ == "__main__":
    print(datetime.datetime.now())
    query_inventory()
