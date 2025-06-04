import os
import pandas as pd
from azure.identity import AzureCliCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta

# Load production resource groups
with open('production_resource_groups.txt') as f:
    prod_groups = set(line.strip().lower() for line in f if line.strip())

# Authenticate
credential = AzureCliCredential()
cost_client = CostManagementClient(credential)

# List subscriptions (using Azure CLI for simplicity)
import subprocess, json
subs = json.loads(subprocess.check_output(['az', 'account', 'list', '-o', 'json']))
results = []

for sub in subs:
    sub_id = sub['id']
    # Set context (optional if using AzureCliCredential)
    # Query cost for last 7 days
    end = datetime.utcnow().date()
    start = end - timedelta(days=7)
    # Query cost for last month (adjust dates as needed)
    # ... (see below for details)
    # Query cost data
    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "time_period": {"from": str(start), "to": str(end)},
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ResourceGroupName"}]
        }
    }
    cost_data = cost_client.query.usage(scope=f"/subscriptions/{sub_id}", parameters=query)
    for row in cost_data.rows:
        rg = row[0].lower()
        cost = row[1]
        results.append({
            "subscription": sub['name'],
            "resource_group": rg,
            "cost": cost,
            "type": "production" if rg in prod_groups else "common"
        })

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("azure_costs_report.csv", index=False)