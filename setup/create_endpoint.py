"""
Create (or update) a Model Serving endpoint for Whisper transcription.

Usage:
    # Uses your default Databricks CLI profile:
    python setup/create_endpoint.py

    # Or specify a profile and catalog/schema:
    DATABRICKS_CONFIG_PROFILE=my-profile CATALOG=my_catalog python setup/create_endpoint.py
"""

import os

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
)

# Configuration — override via environment variables
CATALOG = os.getenv("CATALOG", "my_catalog")
SCHEMA = os.getenv("SCHEMA", "default")
PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE")
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "whisper-transcription")
WORKLOAD_SIZE = os.getenv("WORKLOAD_SIZE", "Medium")
FULL_MODEL_NAME = f"{CATALOG}.{SCHEMA}.whisper_base_transcription"

w = WorkspaceClient(profile=PROFILE) if PROFILE else WorkspaceClient()

print("=" * 70)
print(f"Creating Model Serving endpoint: {ENDPOINT_NAME}")
print("=" * 70)

# Get latest model version
print("\nStep 1: Looking up latest model version...")
versions = list(w.model_versions.list(full_name=FULL_MODEL_NAME))
ready_versions = [v for v in versions if "READY" in str(v.status)]

if not ready_versions:
    print("  No READY model versions found. Checking all versions...")
    for v in versions:
        print(f"    Version {v.version}: {v.status}")
    print("\n  Wait for the model version to become READY, then re-run this script.")
    exit(1)

latest_version = max(ready_versions, key=lambda v: int(v.version))
print(f"  Using version: {latest_version.version}")

# Build config
config = EndpointCoreConfigInput(
    name=ENDPOINT_NAME,
    served_entities=[
        ServedEntityInput(
            entity_name=FULL_MODEL_NAME,
            entity_version=str(latest_version.version),
            workload_size=WORKLOAD_SIZE,
            scale_to_zero_enabled=True,
        )
    ],
)

# Create or update endpoint
print(f"\nStep 2: Creating/updating endpoint '{ENDPOINT_NAME}'...")
try:
    w.serving_endpoints.create(name=ENDPOINT_NAME, config=config)
    print(f"  Endpoint '{ENDPOINT_NAME}' creation initiated.")
except Exception as e:
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        print(f"  Endpoint exists, updating config...")
        w.serving_endpoints.update_config(
            name=ENDPOINT_NAME,
            served_entities=[
                ServedEntityInput(
                    entity_name=FULL_MODEL_NAME,
                    entity_version=str(latest_version.version),
                    workload_size=WORKLOAD_SIZE,
                    scale_to_zero_enabled=True,
                )
            ],
        )
        print(f"  Endpoint '{ENDPOINT_NAME}' config updated.")
    else:
        raise

print(f"\n" + "=" * 70)
print("SUCCESS!")
print("=" * 70)
print(f"\nEndpoint: {ENDPOINT_NAME}")
print(f"Model: {FULL_MODEL_NAME} v{latest_version.version}")
print(f"Workload: {WORKLOAD_SIZE}")
print(f"\nThe endpoint may take 10-15 minutes to become READY.")
print(f"Check status:")
print(f"  databricks serving-endpoints get {ENDPOINT_NAME}")
