# Voice-to-Text Databricks App

A Gradio web app that transcribes audio using OpenAI's [Whisper](https://huggingface.co/openai/whisper-base) model, deployed end-to-end on Databricks.

Users record audio via microphone or upload a file, and the app returns a text transcription powered by a Whisper model running on a Databricks Model Serving endpoint.

<img width="1165" height="394" alt="image" src="https://github.com/user-attachments/assets/717dcabe-3316-42b1-af21-a29fda93bd99" />

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
├── databricks.yml              # Databricks Asset Bundle config
├── resources/
│   └── app.yml                 # Databricks App resource definition
├── app/
│   ├── app.py                  # Gradio UI
│   ├── app.yaml                # App runtime config (command: python app.py)
│   └── requirements.txt        # gradio, databricks-sdk, requests
└── setup/
    ├── register_model.py       # Log Whisper model to MLflow → Unity Catalog
    └── create_endpoint.py      # Create Model Serving endpoint
```

## Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) configured with a profile (`databricks configure`)
- Python 3.11+ with a virtual environment
- A Unity Catalog catalog and schema you have write access to

## Setup

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install "mlflow[databricks]" databricks-sdk pandas numpy
```

### 2. Configure environment

```bash
export DATABRICKS_CONFIG_PROFILE=my-profile   # your CLI profile
export CATALOG=my_catalog                      # Unity Catalog catalog name
export SCHEMA=default                          # schema within the catalog
```

### 3. Register the Whisper model

Logs the Whisper PyFunc model to MLflow and registers it in Unity Catalog as `<catalog>.<schema>.whisper_base_transcription`.

```bash
python setup/register_model.py
```

### 4. Create the serving endpoint

Creates a Model Serving endpoint named `whisper-transcription`. This takes 10-15 minutes to provision.

```bash
python setup/create_endpoint.py
```

Check status:

```bash
databricks serving-endpoints get whisper-transcription
```

### 5. Deploy the Gradio app

```bash
databricks bundle deploy -t dev
```

After deploying, start the app and trigger a source code deployment:

```bash
databricks apps start voice-to-text-dev
databricks apps deploy voice-to-text-dev \
  --source-code-path /Workspace/Users/<your-email>/.bundle/voice-to-text-app/dev/files/app
```

### 6. Grant the app permission to query the endpoint

The app runs as a service principal that needs `CAN_QUERY` on the serving endpoint.

```bash
# Get the app's service principal client ID
databricks apps get voice-to-text-dev

# Get the serving endpoint ID
databricks serving-endpoints get whisper-transcription

# Grant permission (use the endpoint ID and SP client ID from above)
databricks serving-endpoints update-permissions <endpoint-id> \
  --json '{"access_control_list":[{"service_principal_name":"<sp-client-id>","permission_level":"CAN_QUERY"}]}'
```

### 7. Open the app

The app URL is shown in the output of `databricks apps get voice-to-text-dev`. Open it in a browser, upload or record audio, and click **Transcribe**.

## Configuration Reference

All setup scripts read configuration from environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABRICKS_CONFIG_PROFILE` | _(default profile)_ | Databricks CLI profile name |
| `CATALOG` | `my_catalog` | Unity Catalog catalog |
| `SCHEMA` | `default` | Schema within the catalog |
| `ENDPOINT_NAME` | `whisper-transcription` | Name of the serving endpoint |
| `WORKLOAD_SIZE` | `Medium` | Serving endpoint workload size (`Small`, `Medium`, `Large`) |

## Design Decisions

- **`transformers` over `openai-whisper` package** — More robust in serving containers (no ffmpeg dependency)
- **`soundfile` over `librosa`** — Lighter dependency for audio I/O, reduces container memory usage
- **`whisper-base` (74M params)** — Good speed/accuracy balance; swap for `whisper-small` or `whisper-medium` for better accuracy
- **Base64 audio transport** — Reliable way to send audio bytes over HTTP to a serving endpoint
- **Medium workload size** — `Small` (4GB) is insufficient for torch + Whisper inference; `Medium` provides enough headroom
- **Databricks SDK `authenticate()` for auth** — Works with both PAT tokens and OAuth (required in Databricks Apps runtime)
