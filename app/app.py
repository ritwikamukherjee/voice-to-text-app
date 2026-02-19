"""
Gradio voice-to-text UI. Calls the Whisper Model Serving endpoint.

Run from repo root: python app/app.py
Or in Databricks: point the App at the repo root, start command: python app/app.py
"""

import base64
import os
import sys

# Prefer config from repo root (when run from repo); fallback to env when only app/ is deployed (e.g. Databricks App)
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
try:
    from config import ENDPOINT_NAME
except ImportError:
    ENDPOINT_NAME = os.getenv("ENDPOINT_NAME", "whisper-transcription")

import gradio as gr
import requests
from databricks.sdk import WorkspaceClient


def transcribe(audio_path: str) -> str:
    if audio_path is None:
        return "No audio provided. Record or upload a file."

    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
    except Exception as e:
        return f"Error reading file: {e}"

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    w = WorkspaceClient()
    host = w.config.host.rstrip("/")
    url = f"{host}/serving-endpoints/{ENDPOINT_NAME}/invocations"
    headers = {"Content-Type": "application/json"}
    for k, v in w.config.authenticate().items():
        headers[k] = v
    payload = {"dataframe_records": [{"audio_base64": audio_b64}]}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.HTTPError:
        return f"Endpoint error ({resp.status_code}): {resp.text}"
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

    data = resp.json()
    if "predictions" in data and isinstance(data["predictions"], list) and data["predictions"]:
        pred = data["predictions"][0]
        if isinstance(pred, dict) and "transcription" in pred:
            return pred["transcription"]
        return str(pred)
    return str(data)


with gr.Blocks(title="Voice to Text") as demo:
    gr.Markdown("# Voice to Text\nWhisper on Databricks Model Serving")
    with gr.Row():
        with gr.Column():
            audio_input = gr.Audio(sources=["upload", "microphone"], type="filepath", label="Audio")
            transcribe_btn = gr.Button("Transcribe", variant="primary")
        with gr.Column():
            output_text = gr.Textbox(label="Transcription", lines=8, interactive=False)
    transcribe_btn.click(fn=transcribe, inputs=audio_input, outputs=output_text)

port = int(os.getenv("DATABRICKS_APP_PORT", "7860"))
demo.launch(server_name="0.0.0.0", server_port=port)
