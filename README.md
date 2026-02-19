# Voice-to-Text Databricks App

A Gradio web app that transcribes audio using OpenAI's [Whisper](https://huggingface.co/openai/whisper-base) model, deployed end-to-end on Databricks.

Users record audio via microphone or upload a file, and the app returns a text transcription powered by a Whisper model running on a Databricks Model Serving endpoint.

<img width="1165" height="394" alt="Voice-to-Text app" src="https://github.com/user-attachments/assets/717dcabe-3316-42b1-af21-a29fda93bd99" />

> **Disclaimer:** This project is a solution accelerator. It is provided as-is for reference and experimentation. Use and adapt it to your own environment and requirements; it is not an officially supported product.

## Architecture

```
User (browser)
  │
  ▼
Gradio App (Databricks Apps)
  │  base64-encoded audio
  ▼
Model Serving Endpoint
  │  Whisper PyFunc inference
  ▼
Transcription text returned
```

**Key components:**

- **Whisper PyFunc model** — `openai/whisper-base` (74M params) wrapped as an MLflow PyFunc, registered in Unity Catalog
- **Model Serving endpoint** — Hosts the model with scale-to-zero, accepts base64-encoded audio via REST API
- **Gradio app** — Deployed as a Databricks App, authenticates to the serving endpoint via the Databricks SDK

## Project Structure

```
voice-to-text-app/
├── config.py                  # Catalog, schema, endpoint (edit or set via env/widgets)
├── register_model.py          # Log Whisper model to MLflow → Unity Catalog
├── create_endpoint.py         # Create Model Serving endpoint
├── Setup.ipynb                # One-time setup notebook (widgets for catalog/schema)
├── requirements.txt           # Setup deps: mlflow, databricks-sdk, torch, transformers, etc.
└── app/
    ├── app.py                 # Gradio UI
    └── requirements.txt      # gradio, databricks-sdk, requests
```

## Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) (optional for local setup; configure with `databricks configure`)
- Python 3.11+ (for local run or cluster running the setup notebook)
- A Unity Catalog catalog and schema you have write access to
- Clone the repo via **git** or **Databricks Repos** (do not rely on manual uploads)

## Setup

### 1. Get the code

```bash
git clone https://github.com/ritwikamukherjee/voice-to-text-app.git
```

In Databricks: **Repos** → **Add repo** → use the repo URL, or clone into a workspace path.

### 2. Configure catalog and schema

Set **CATALOG** and **SCHEMA** (and optionally **ENDPOINT_NAME**) before running setup or the app.

- **Option A — Edit `config.py`:** Set `CATALOG`, `SCHEMA`, and optionally `ENDPOINT_NAME`.
- **Option B — Environment variables / notebook widgets (recommended):** In **Setup.ipynb**, use the **Catalog** and **Schema** text widgets in the first code cell; they set the environment for the rest of the notebook. You can also set `CATALOG` and `SCHEMA` in your shell or notebook environment.

If you run `register_model.py` or `create_endpoint.py` without setting these, the scripts exit with a clear message asking you to configure them.

### 3. One-time setup (run the notebook)

1. Open **Setup.ipynb** in the cloned repo (in your workspace or locally).
2. In the first code cell, enter your **Catalog** and **Schema** in the widgets, and set **REPO_PATH** to the path where the repo lives (e.g. `/Workspace/Users/<your-email>/voice-to-text-app` or your Repos path).
3. Run the first cell to apply widgets and path.
4. Attach a cluster and run the rest of the notebook in order:
   - **Register Whisper model** — run the cell; wait until you see `Registered: ... version N`.
   - Wait for the model to be **READY** in **Catalog** (your catalog → schema → `whisper_base_transcription`).
   - **Create serving endpoint** — run the cell; wait **10–15 minutes** until the endpoint is **READY** under **Serving**.

### 4. Deploy the Gradio app (Databricks App)

When the endpoint is **READY**, run the app as a **Databricks App**. See the [Databricks Apps get-started guide](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started).

1. In your workspace, click **+ New** → **App** (or **Apps** → **Create app**).
2. **Source:** point the app at the **repo root** (the cloned folder that contains `app/` and `config.py`).
3. **Start command:** `python app/app.py`
4. Set **Requirements** to **app/requirements.txt** if the UI allows; otherwise the app runtime can use the root **requirements.txt**.
5. Create/install the app. It will start and show an **app URL** on the Overview page.
6. Click the URL to open the app. Grant the app **Can query** on the **whisper-transcription** serving endpoint (Serving → endpoint → Permissions).

To re-deploy after code changes, use the **Deploy** action or the deploy command on the app Overview page.

### 5. Open the app

Open the app URL from the app Overview page, upload or record audio, and click **Transcribe**.

## Configuration Reference

Setup scripts and the app read configuration from **config.py** or environment variables:

| Variable | Description |
|----------|-------------|
| `CATALOG` | Unity Catalog catalog (required; set in config.py, env, or notebook widgets) |
| `SCHEMA` | Schema within the catalog (required) |
| `ENDPOINT_NAME` | Name of the serving endpoint (default: `whisper-transcription`) |
| `WORKLOAD_SIZE` | Serving endpoint size: `Small`, `Medium`, `Large` (default: `Medium`) |
| `DATABRICKS_CONFIG_PROFILE` | Databricks CLI profile name (optional, for local run) |

## Design Decisions

- **`transformers` over `openai-whisper` package** — More robust in serving containers (no ffmpeg dependency)
- **`soundfile` over `librosa`** — Lighter dependency for audio I/O, reduces container memory usage
- **`whisper-base` (74M params)** — Good speed/accuracy balance; swap for `whisper-small` or `whisper-medium` for better accuracy
- **Base64 audio transport** — Reliable way to send audio bytes over HTTP to a serving endpoint
- **Medium workload size** — `Small` (4GB) is insufficient for torch + Whisper inference; `Medium` provides enough headroom
- **Databricks SDK `authenticate()` for auth** — Works with both PAT tokens and OAuth (required in Databricks Apps runtime)

## Run locally (optional)

Running the app locally is optional and for **development and debugging**. The primary way to run is as a Databricks App (see above).

1. Clone and enter the repo, then set **CATALOG** and **SCHEMA** in `config.py` or via `export CATALOG=... SCHEMA=...`.
2. One-time setup (Databricks CLI configured): `pip install -r requirements.txt`, then `python register_model.py`, then `python create_endpoint.py`. Wait for model and endpoint READY; grant **Can query** on the endpoint if needed.
3. Run the app: `pip install -r app/requirements.txt`, then `python app/app.py`. Open `http://localhost:7860`.

Alternatively, use the [get-started guide](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started) to sync and run `databricks apps run-local --prepare-environment --debug`, then re-deploy from the app Overview page.
