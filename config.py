"""
Single place for catalog, schema, and endpoint config.
Edit this file only; all other scripts read from here.
"""

import os

# Unity Catalog
CATALOG = os.getenv("CATALOG", "hls_amer_catalog")
SCHEMA = os.getenv("SCHEMA", "voice-to-text")

# Model (used by register_model and create_endpoint)
MODEL_NAME = "whisper_base_transcription"
FULL_MODEL_NAME = f"{CATALOG}.{SCHEMA}.{MODEL_NAME}"

# Model Serving endpoint (used by create_endpoint and app)
ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "whisper-transcription")
WORKLOAD_SIZE = os.getenv("WORKLOAD_SIZE", "Medium")

# Optional: Databricks CLI profile when running locally
PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE")
