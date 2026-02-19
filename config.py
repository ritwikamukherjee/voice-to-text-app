"""
Configuration for the voice-to-text app. You must set CATALOG and SCHEMA
before running register_model.py or create_endpoint.py.

Set them here or via environment variables (CATALOG, SCHEMA, ENDPOINT_NAME, etc.).
No workspace names or user emails are hardcoded.
"""

import os
import sys

# Unity Catalog — set these (edit below or set env vars CATALOG, SCHEMA)
CATALOG = os.getenv("CATALOG", "").strip()
SCHEMA = os.getenv("SCHEMA", "").strip()

# Model name (fixed); full name is built from catalog + schema
MODEL_NAME = "whisper_base_transcription"
FULL_MODEL_NAME = f"{CATALOG}.{SCHEMA}.{MODEL_NAME}" if (CATALOG and SCHEMA) else ""

# Model Serving endpoint — set if different from default
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "whisper-transcription").strip() or "whisper-transcription"
WORKLOAD_SIZE = os.getenv("WORKLOAD_SIZE", "Medium").strip() or "Medium"

# Optional: Databricks CLI profile when running locally
PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE", "").strip() or None


def require_catalog_schema():
    """Call before register_model or create_endpoint. Exits with a clear message if not configured."""
    if not CATALOG or not SCHEMA:
        print(
            "Configuration required: set CATALOG and SCHEMA in config.py or set the\n"
            "environment variables CATALOG and SCHEMA to your Unity Catalog catalog and schema."
        )
        sys.exit(1)
