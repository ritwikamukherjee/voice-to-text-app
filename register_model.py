"""
Register Whisper speech-to-text model as an MLflow PyFunc in Unity Catalog.
Model: openai/whisper-base (74M params)

Run in Databricks: create a notebook, attach a cluster, then run this file
(e.g. %run /Workspace/Users/<you>/voice-to-text-app/register_model).
Or run locally with: python register_model.py
"""

import mlflow
import pandas as pd
import numpy as np
import base64
import io

from databricks.sdk import WorkspaceClient

from config import CATALOG, SCHEMA, MODEL_NAME, FULL_MODEL_NAME, PROFILE


class WhisperTranscriptionModel(mlflow.pyfunc.PythonModel):
    """Whisper as MLflow PyFunc. Input: DataFrame with 'audio_base64'. Output: 'transcription'."""

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
            if len(audio_array.shape) > 1:
                audio_array = audio_array.mean(axis=1)
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


# --- Main ---
print("Registering Whisper model to Unity Catalog...")

w = WorkspaceClient(profile=PROFILE) if PROFILE else WorkspaceClient()

# Clean pending versions
try:
    versions = list(w.model_versions.list(full_name=FULL_MODEL_NAME))
    for v in versions:
        if "PENDING" in str(v.status):
            try:
                w.model_versions.delete(full_name=FULL_MODEL_NAME, version=str(v.version))
            except Exception:
                pass
except Exception:
    pass

tracking_uri = f"databricks://{PROFILE}" if PROFILE else "databricks"
mlflow.set_tracking_uri(tracking_uri)
mlflow.set_registry_uri("databricks-uc")

experiment_name = f"/Users/{w.current_user.me().user_name}/whisper_transcription"
try:
    mlflow.create_experiment(experiment_name)
except Exception as e:
    if "already exists" not in str(e).lower():
        raise
mlflow.set_experiment(experiment_name)

model = WhisperTranscriptionModel()
example_input = pd.DataFrame({"audio_base64": ["<base64>"]})
example_output = pd.DataFrame({"transcription": ["Hello."]})
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
    model_uri = f"runs:/{run.info.run_id}/model"

model_version_info = mlflow.register_model(model_uri=model_uri, name=FULL_MODEL_NAME)
print(f"Registered: {FULL_MODEL_NAME} version {model_version_info.version}")
print("Next: run create_endpoint.py (then wait ~10–15 min for endpoint READY)")
