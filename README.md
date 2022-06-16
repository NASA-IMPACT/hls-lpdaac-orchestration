# HLS LPDAAC ORCHESTRATION MANUAL IMPLEMENTATION

This branch allows for the manual trigger of the reconciliation process for both forward and historical processing.

## Description of configuration

* `table_params.txt` - If the table does not exist in AWS athena, this is the template for creating a new one. Note that the Table Name and Location are formatted within the code using the `inventory_locations.json` file

* `inventory_locations.json` - This is a list of table names and the s3 path to their hive directories. If creating a new table, you must use the table name as the key and the path to the s3 path to the hive directory as the value for the script to work properly

* `database_params.json` - This is the database configuration that looks for the table in athena. If the table does not exist in the database, a new one will be created if the hive directory is provided in the `inventory_locations.json` file. The output location in the json file corresponds to the output of the athena query.

## Executables

* `make_report_athena.py` - This is the main executable and requires an input start date formatted as `yyyyddd` (e.g. 2022151). By default, the code is configured to query for a single day at a time (e.g. 2022151 - 2022152) and the query is based on the last modified date in AWS.

* `reconcile.sh` - This is a simple shell wrapper to run through multiple manual reconciliation triggers at a time (i.e. multiple days). There is 40-minute lag between reconciliation triggers to limit the load on LPDAAC ingest workflow.
