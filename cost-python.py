import os
import pandas as pd
from azure.identity import AzureCliCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta, UTC

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
    end = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=30)
    time_period = {
        "from": start.isoformat().replace("+00:00", "Z"),
        "to": end.isoformat().replace("+00:00", "Z")
    }
    query = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "time_period": time_period,
        "dataset": {
            "granularity": "None",
            "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
            "grouping": [{"type": "Dimension", "name": "ResourceGroupName"}]
        }
    }
    cost_data = cost_client.query.usage(scope=f"/subscriptions/{sub_id}", parameters=query)
    for row in cost_data.rows:
        # print(row)  # Uncomment to debug structure
        cost = row[0]
        rg_raw = row[1] if len(row) > 1 else None
        rg = str(rg_raw).lower() if isinstance(rg_raw, str) else "unknown"
        results.append({
            "subscription": sub['name'],
            "resource_group": rg,
            "cost": cost,
            "type": "production" if rg in prod_groups else "common"
        })

# Save to CSV
df = pd.DataFrame(results)
df.to_csv("azure_costs_report.csv", index=False)