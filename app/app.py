"""
Gradio voice-to-text app powered by a Whisper Model Serving endpoint.

Deployed as a Databricks App. Uses WorkspaceClient for auth (auto-authenticates
in the Databricks Apps runtime).
"""

import base64
import os

import gradio as gr
import requests
from databricks.sdk import WorkspaceClient

ENDPOINT_NAME = "whisper-transcription"


def get_workspace_client():
    """Get authenticated WorkspaceClient (auto-auth in Databricks Apps runtime)."""
    return WorkspaceClient()


def transcribe(audio_path: str) -> str:
    """Read audio file, base64-encode, send to serving endpoint, return text."""
    if audio_path is None:
        return "No audio provided. Please record or upload an audio file."

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
    except Exception as e:
        return f"Error reading audio file: {e}"

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    w = get_workspace_client()
    host = w.config.host.rstrip("/")

    url = f"{host}/serving-endpoints/{ENDPOINT_NAME}/invocations"

    # Get auth headers from the SDK (supports OAuth in Apps runtime)
    headers = {"Content-Type": "application/json"}
    header_factory = w.config.authenticate
    for key, value in header_factory().items():
        headers[key] = value

    payload = {
        "dataframe_records": [{"audio_base64": audio_b64}]
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        return f"Serving endpoint error ({resp.status_code}): {resp.text}"
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

    data = resp.json()

    # Model Serving returns {"predictions": [{"transcription": "..."}]}
    if "predictions" in data:
        predictions = data["predictions"]
        if isinstance(predictions, list) and len(predictions) > 0:
            pred = predictions[0]
            if isinstance(pred, dict) and "transcription" in pred:
                return pred["transcription"]
            return str(pred)
        return str(predictions)

    return str(data)


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="Voice to Text") as demo:
    gr.Markdown("# Voice to Text\nTranscribe audio using Whisper on Databricks Model Serving.")

    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Audio Input",
            )
            transcribe_btn = gr.Button("Transcribe", variant="primary")

        with gr.Column():
            output_text = gr.Textbox(
                label="Transcription",
                lines=8,
                interactive=False,
            )

    transcribe_btn.click(fn=transcribe, inputs=audio_input, outputs=output_text)

port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))
demo.launch(server_name="0.0.0.0", server_port=port, share=False)
