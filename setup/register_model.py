"""
Register Whisper speech-to-text model as an MLflow PyFunc in Unity Catalog.

Model: openai/whisper-base (74M params)

Usage:
    # Uses your default Databricks CLI profile:
    python setup/register_model.py

    # Or specify a profile:
    DATABRICKS_CONFIG_PROFILE=my-profile python setup/register_model.py

    # Or set catalog/schema:
    CATALOG=my_catalog SCHEMA=my_schema python setup/register_model.py
"""

import os
import mlflow
import pandas as pd
import numpy as np
import base64
import io

from databricks.sdk import WorkspaceClient


# Configuration — override via environment variables
CATALOG = os.getenv("CATALOG", "my_catalog")
SCHEMA = os.getenv("SCHEMA", "default")
MODEL_NAME = "whisper_base_transcription"
FULL_MODEL_NAME = f"{CATALOG}.{SCHEMA}.{MODEL_NAME}"
PROFILE = os.getenv("DATABRICKS_CONFIG_PROFILE")


class WhisperTranscriptionModel(mlflow.pyfunc.PythonModel):
    """Whisper speech-to-text model wrapped as MLflow PyFunc.

    Accepts a DataFrame with an `audio_base64` column containing
    base64-encoded audio bytes. Returns a DataFrame with a
    `transcription` column.
    """

    def load_context(self, context):
        import torch
        from transformers import WhisperProcessor, WhisperForConditionalGeneration

        self.device = "cpu"
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-base")
        self.model = WhisperForConditionalGeneration.from_pretrained(
            "openai/whisper-base", torch_dtype=torch.float32
        ).to(self.device)
        self.model.eval()

    def predict(self, context, model_input):
        import torch
        import soundfile as sf

        if isinstance(model_input, pd.DataFrame):
            audio_b64_list = model_input["audio_base64"].tolist()
        else:
            raise ValueError("Input must be a DataFrame with an 'audio_base64' column")

        results = []
        for audio_b64 in audio_b64_list:
            audio_bytes = base64.b64decode(audio_b64)
            audio_array, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")

            # Convert stereo to mono if needed
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)

            # Resample to 16kHz if needed
            if sr != 16000:
                duration = len(audio_array) / sr
                target_len = int(duration * 16000)
                audio_array = np.interp(
                    np.linspace(0, len(audio_array) - 1, target_len),
                    np.arange(len(audio_array)),
                    audio_array,
                ).astype(np.float32)

            input_features = self.processor(
                audio_array, sampling_rate=16000, return_tensors="pt"
            ).input_features.to(self.device)

            with torch.no_grad():
                predicted_ids = self.model.generate(input_features)

            transcription = self.processor.batch_decode(
                predicted_ids, skip_special_tokens=True
            )[0]
            results.append(transcription)

        return pd.DataFrame({"transcription": results})


# ---------------------------------------------------------------------------
# Main registration flow
# ---------------------------------------------------------------------------

print("=" * 70)
print("Registering Whisper Model to Unity Catalog via MLflow")
print("=" * 70)

# Step 1: Clean up pending versions
print("\nStep 1: Checking for pending model versions...")
w = WorkspaceClient(profile=PROFILE) if PROFILE else WorkspaceClient()

try:
    versions = list(w.model_versions.list(full_name=FULL_MODEL_NAME))
    pending_versions = [v for v in versions if "PENDING" in str(v.status)]
    if pending_versions:
        print(f"  Found {len(pending_versions)} pending version(s) - deleting...")
        for v in pending_versions:
            try:
                w.model_versions.delete(full_name=FULL_MODEL_NAME, version=str(v.version))
                print(f"  Deleted version {v.version}")
            except Exception as e:
                print(f"  Could not delete version {v.version}: {e}")
    else:
        print("  No pending versions found")
except Exception as e:
    print(f"  Model may not exist yet: {e}")

# Step 2: Configure MLflow for Unity Catalog
print("\nStep 2: Configuring MLflow for Unity Catalog...")
tracking_uri = f"databricks://{PROFILE}" if PROFILE else "databricks"
mlflow.set_tracking_uri(tracking_uri)
mlflow.set_registry_uri("databricks-uc")
print(f"  Tracking URI: {tracking_uri}")
print(f"  Registry URI: databricks-uc")

# Step 3: Create / set experiment
print("\nStep 3: Setting up MLflow experiment...")
experiment_name = f"/Users/{w.current_user.me().user_name}/whisper_transcription"
try:
    experiment_id = mlflow.create_experiment(experiment_name)
    print(f"  Created experiment: {experiment_name}")
except Exception as e:
    if "already exists" in str(e).lower():
        experiment_id = mlflow.get_experiment_by_name(experiment_name).experiment_id
        print(f"  Using existing experiment: {experiment_name}")
    else:
        raise
mlflow.set_experiment(experiment_name)

# Step 4: Log model
print("\nStep 4: Logging Whisper model to MLflow...")

model = WhisperTranscriptionModel()

example_input = pd.DataFrame({"audio_base64": ["<base64-encoded-audio>"]})
example_output = pd.DataFrame({"transcription": ["Hello, this is a test."]})
signature = mlflow.models.infer_signature(example_input, example_output)

with mlflow.start_run() as run:
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=model,
        signature=signature,
        pip_requirements=[
            "transformers>=4.36.0",
            "torch>=2.0.0",
            "soundfile>=0.12.0",
            "pandas>=1.5.0",
            "numpy>=1.23.0",
        ],
    )
    run_id = run.info.run_id
    model_uri = f"runs:/{run_id}/model"
    print(f"  Model logged with run_id: {run_id}")

# Step 5: Register to Unity Catalog
print("\nStep 5: Registering model to Unity Catalog...")
try:
    model_version_info = mlflow.register_model(
        model_uri=model_uri,
        name=FULL_MODEL_NAME,
    )
    print(f"  Model registered successfully!")
    print(f"  Name: {model_version_info.name}")
    print(f"  Version: {model_version_info.version}")

    print("\n" + "=" * 70)
    print("SUCCESS!")
    print("=" * 70)
    print(f"\nModel: {FULL_MODEL_NAME}")
    print(f"Version: {model_version_info.version}")
    print(f"\nNext step:")
    print(f"  python setup/create_endpoint.py")

except Exception as e:
    print(f"\nError during registration: {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Ensure catalog/schema exist: {CATALOG}.{SCHEMA}")
    print(f"  2. Check permissions on the catalog")
    print(f"  3. Verify your Databricks CLI profile is configured")
