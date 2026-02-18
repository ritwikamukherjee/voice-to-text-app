"""
Create a Model Serving endpoint for the Whisper model.

Run after register_model.py, once the model version is READY.
In Databricks: %run /Workspace/Users/<you>/voice-to-text-app/create_endpoint
"""

import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput

CATALOG = os.getenv("CATALOG", "main")
SCHEMA = os.getenv("SCHEMA", "default")
PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE")
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "whisper-transcription")
WORKLOAD_SIZE = os.getenv("WORKLOAD_SIZE", "Medium")
FULL_MODEL_NAME = f"{CATALOG}.{SCHEMA}.whisper_base_transcription"

w = WorkspaceClient(profile=PROFILE) if PROFILE else WorkspaceClient()

versions = list(w.model_versions.list(full_name=FULL_MODEL_NAME))
ready = [v for v in versions if "READY" in str(v.status)]
if not ready:
    print("No READY model version. Run register_model.py and wait for READY.")
    exit(1)

latest = max(ready, key=lambda v: int(v.version))
config = EndpointCoreConfigInput(
    name=ENDPOINT_NAME,
    served_entities=[
        ServedEntityInput(
            entity_name=FULL_MODEL_NAME,
            entity_version=str(latest.version),
            workload_size=WORKLOAD_SIZE,
            scale_to_zero_enabled=True,
        )
    ],
)

try:
    w.serving_endpoints.create(name=ENDPOINT_NAME, config=config)
    print(f"Endpoint '{ENDPOINT_NAME}' creation started.")
except Exception as e:
    if "already exists" in str(e).lower() or "RESOURCE_ALREADY_EXISTS" in str(e):
        w.serving_endpoints.update_config(
            name=ENDPOINT_NAME,
            served_entities=[
                ServedEntityInput(
                    entity_name=FULL_MODEL_NAME,
                    entity_version=str(latest.version),
                    workload_size=WORKLOAD_SIZE,
                    scale_to_zero_enabled=True,
                )
            ],
        )
        print(f"Endpoint '{ENDPOINT_NAME}' updated.")
    else:
        raise

print(f"Endpoint may take 10–15 min to become READY. Then run the app.")
