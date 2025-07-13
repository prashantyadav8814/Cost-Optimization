### Azure Billing Cost Optimization - Serverless Architecture

# Folder: functions/archive_old_records.py
import datetime
import json
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient

def archive_old_billing_records():
    cosmos_client = CosmosClient(COSMOS_URI, COSMOS_KEY)
    container = cosmos_client.get_database_client('BillingDB').get_container_client('Records')

    blob_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    blob_container = blob_client.get_container_client("archived-records")

    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
    archived = []

    for item in container.query_items(
        query="SELECT * FROM c WHERE c.timestamp < @cutoff",
        parameters=[{"name": "@cutoff", "value": cutoff_date.isoformat()}],
        enable_cross_partition_query=True
    ):
        blob_name = f"{item['id']}.json"
        blob_container.upload_blob(blob_name, data=json.dumps(item), overwrite=True)
        container.delete_item(item, partition_key=item['partitionKey'])
        archived.append(item['id'])

    print(f"Archived {len(archived)} items.")


# Folder: functions/get_billing_record.py
from azure.cosmos import CosmosClient, exceptions
from azure.storage.blob import BlobServiceClient
import json

def get_billing_record(record_id):
    cosmos_client = CosmosClient(COSMOS_URI, COSMOS_KEY)
    container = cosmos_client.get_database_client('BillingDB').get_container_client('Records')

    blob_client = BlobServiceClient.from_connection_string(BLOB_CONN_STR)
    blob_container = blob_client.get_container_client("archived-records")

    try:
        return container.read_item(record_id, partition_key=extract_partition_key(record_id))
    except exceptions.CosmosResourceNotFoundError:
        blob_name = f"{record_id}.json"
        blob_data = blob_container.get_blob_client(blob_name).download_blob().readall()
        return json.loads(blob_data)


def extract_partition_key(record_id):
    # Placeholder function
    return record_id[:2]  # Example logic


# Folder: README.md
"""
# Azure Cost Optimization for Billing Records

## Overview
This solution archives old billing records from Cosmos DB to Azure Blob Storage to reduce cost, without changing existing APIs or causing downtime.

## Architecture
![Architecture Diagram](architecture.png)

## Components
- Azure Cosmos DB: Stores recent billing records (<3 months)
- Azure Blob Storage: Stores archived records as JSON
- Azure Functions:
  - `archive_old_billing_records`: Moves old data to Blob
  - `get_billing_record`: Transparently retrieves from Cosmos or Blob

## How to Deploy
1. Set up environment variables:
   - `COSMOS_URI`
   - `COSMOS_KEY`
   - `BLOB_CONN_STR`
2. Deploy the functions using Azure CLI or Visual Studio Code
3. Schedule `archive_old_billing_records` using a Timer Trigger (e.g., weekly)

## Cost Savings
Move cold data (~90% of volume) from Cosmos DB (~$300/month) to Blob (~$10/month), with fallback logic to serve archived data.
"""


# Folder: architecture.png
# [Include a diagram showing Billing API -> Azure Function -> Cosmos DB or Blob Storage fallback]
# You can draw this manually and upload to GitHub.

# Optional: deployment/bicep/main.bicep or Terraform templates for Infra as Code
