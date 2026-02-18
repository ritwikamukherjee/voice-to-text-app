# Voice-to-Text App

Whisper transcription on Databricks: register model → create endpoint → run Gradio app. No bundles, just code.

## Upload to workspace

1. In Databricks, go to **Workspace** → your user folder.
2. Create a folder (e.g. `voice-to-text-app`) and upload:
   - `register_model.py`
   - `create_endpoint.py`
   - `app.py`
   - `requirements.txt`

Or use **Repos** and clone this repo into the workspace.

---

## Setup (one-time)

### 1. Register the Whisper model

- Create a **notebook** in the same workspace (or in the folder above).
- Attach a **cluster** (single node is enough; GPU speeds up the first run).
- In the notebook, set your catalog/schema and run the script:

```python
# Cell 1: config (edit catalog/schema if needed)
import os
os.environ["CATALOG"] = "main"   # your Unity Catalog catalog
os.environ["SCHEMA"] = "default"

# Cell 2: run the registration script
%run /Workspace/Users/<your-email>/voice-to-text-app/register_model
```

- Install dependencies on the cluster if needed: `pip install mlflow databricks-sdk pandas numpy transformers torch soundfile` (or use a cluster with these libs).

### 2. Create the serving endpoint

- After the model is **READY** in the catalog (check in **Catalog** → your catalog → schema → model), run:

```python
%run /Workspace/Users/<your-email>/voice-to-text-app/create_endpoint
```

- Wait **10–15 minutes** until the endpoint status is **READY** (Serving → your endpoint).

### 3. Run the Gradio app

- Create a **new notebook**, attach the **same cluster** (or any cluster with `gradio`, `requests`, `databricks-sdk`).
- Run:

```python
%run /Workspace/Users/<your-email>/voice-to-text-app/app
```

- Click the **gradio.live** (or similar) URL shown in the cell output to open the app. Record or upload audio and click **Transcribe**.

---

## Config (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `CATALOG` | `main` | Unity Catalog catalog |
| `SCHEMA` | `default` | Schema name |
| `ENDPOINT_NAME` | `whisper-transcription` | Serving endpoint name |
| `WORKLOAD_SIZE` | `Medium` | Endpoint size |
| `DATABRICKS_CONFIG_PROFILE` | (default) | CLI profile when run locally |

---

## Run locally (optional)

With Databricks CLI configured (`databricks configure`):

```bash
pip install -r requirements.txt
export CATALOG=main SCHEMA=default
python register_model.py
python create_endpoint.py
# wait for endpoint READY, then:
python app.py
# open http://localhost:7860
```
