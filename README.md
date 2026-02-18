# Voice-to-Text App

Whisper transcription on Databricks: one-time setup (notebook) → then run the Gradio app. No bundles, just code.

---

## Config (one file)

All catalog, schema, and endpoint settings live in **`config.py`**. Edit that file only; the rest of the code reads from it.

| Setting | Default | Description |
|--------|---------|-------------|
| `CATALOG` | `hls_amer_catalog` | Unity Catalog catalog |
| `SCHEMA` | `voice-to-text` | Schema name |
| `ENDPOINT_NAME` | `whisper-transcription` | Model Serving endpoint name |
| `WORKLOAD_SIZE` | `Medium` | Endpoint size |

You can still override with environment variables (e.g. `CATALOG`, `SCHEMA`) if needed.

---

## Upload to workspace

Upload this folder to your Databricks workspace (e.g. **Workspace** → **Users** → **&lt;you&gt;** → **voice-to-text-app**). Include:

- **config.py**
- **register_model.py**
- **create_endpoint.py**
- **app/** (folder with **app.py** and **requirements.txt**)
- **Setup.ipynb**
- **requirements.txt** (for setup / cluster libs)

---

## One-time setup (run the notebook)

1. Open **Setup.ipynb** in that folder.
2. In the first code cell, set **REPO_PATH** if your folder is not at:
   `/Workspace/Users/raven.mukherjee@databricks.com/voice-to-text-app`
3. Attach a **cluster** and run the notebook **Run all** (or run cells in order).
4. After **1. Register Whisper model**: wait until the model is **READY** in **Catalog** (your catalog → schema → `whisper_base_transcription`).
5. Run **2. Create serving endpoint**. Wait **10–15 minutes** until the endpoint is **READY** under **Serving**.

No `%run` of `.py` files; the notebook uses `runpy` to execute the scripts.

---

## Run the app

When the endpoint is **READY**, you can run the Gradio UI in either of these ways.

### Option A – From a notebook

In a new notebook (same folder or same path on `sys.path):

```python
REPO_PATH = "/Workspace/Users/raven.mukherjee@databricks.com/voice-to-text-app"
import sys
sys.path.insert(0, REPO_PATH)
import runpy
runpy.run_path(REPO_PATH + "/app/app.py", run_name="__main__")
```

Then open the URL shown in the output.

### Option B – As a Databricks App

1. In Databricks: **Apps** → **Create app**.
2. Set **Source** to the **repo root** (the folder that contains `app/` and `config.py`).
3. **Start command:** `python app/app.py`
4. Use **app/requirements.txt** for the app’s dependencies (gradio, requests, databricks-sdk) if the UI lets you set a requirements path; otherwise the root **requirements.txt** is fine.
5. Start the app and open the URL provided.

---

## Run locally (optional)

With Databricks CLI configured (`databricks configure`):

```bash
pip install -r requirements.txt
python register_model.py
python create_endpoint.py
# wait for endpoint READY, then:
pip install -r app/requirements.txt
python app/app.py
# open http://localhost:7860
```

Config is read from **config.py** (or override with env vars).
