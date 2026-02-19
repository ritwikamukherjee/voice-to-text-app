# Voice-to-Text App

Whisper transcription on Databricks: one-time setup (notebook) → then run the Gradio app. No bundles, just code. No catalog, schema, or workspace names are hardcoded — you configure them.

---

## Configuration (required before running)

Set your Unity Catalog **catalog** and **schema** (and optionally endpoint name) before running any setup or the app.

**Option 1 – Edit `config.py`**

Open **config.py** and set:

- `CATALOG` — your Unity Catalog catalog name  
- `SCHEMA` — your schema name (e.g. the schema where the model will live)  
- `ENDPOINT_NAME` — (optional) Model Serving endpoint name; default is `whisper-transcription`

**Option 2 – Environment variables**

Set `CATALOG` and `SCHEMA` (and optionally `ENDPOINT_NAME`) in your environment or in the notebook before running the scripts.

If you run register_model or create_endpoint without setting these, the scripts will exit with a clear message asking you to configure them.

---

## Upload to workspace

Upload this folder to your Databricks workspace (e.g. **Workspace** → **Users** → **&lt;you&gt;** → **voice-to-text-app**). Include:

- **config.py** (and set CATALOG / SCHEMA as above)
- **register_model.py**
- **create_endpoint.py**
- **app/** (folder with **app.py** and **requirements.txt**)
- **Setup.ipynb**
- **requirements.txt** (for setup / cluster libs)

---

## One-time setup (run the notebook)

1. Open **Setup.ipynb** in that folder.
2. In the first code cell, enter your **Catalog** and **Schema** in the widgets, and set **REPO_PATH** to your workspace folder path (e.g. `/Workspace/Users/&lt;your-email&gt;/voice-to-text-app`).
3. Attach a **cluster** and run the notebook (Run all or run cells in order).
5. After **1. Register Whisper model**: wait until the model is **READY** in **Catalog** (your catalog → schema → `whisper_base_transcription`).
6. Run **2. Create serving endpoint**. Wait **10–15 minutes** until the endpoint is **READY** under **Serving**.

---

## Run the app

When the endpoint is **READY**, run the Gradio UI from a notebook or deploy as a Databricks App (see README sections below). Set **ENDPOINT_NAME** in config or env if you used a different endpoint name.

### Option A – From a notebook

```python
REPO_PATH = "/Workspace/Users/<your-email>/voice-to-text-app"  # your path
import sys
sys.path.insert(0, REPO_PATH)
import runpy
runpy.run_path(REPO_PATH + "/app/app.py", run_name="__main__")
```

Then open the URL shown in the output.

### Option B – As a Databricks App

1. **Apps** → **Create app**.
2. **Source:** repo root (folder that contains `app/` and `config.py`).
3. **Start command:** `python app/app.py`
4. Use **app/requirements.txt** for dependencies if the UI allows; otherwise root **requirements.txt**.
5. Start the app and open the URL. Ensure the app has **Can query** on the serving endpoint.

---

## Run locally (optional)

With Databricks CLI configured (`databricks configure`), set **CATALOG** and **SCHEMA** in config or env, then:

```bash
pip install -r requirements.txt
python register_model.py
python create_endpoint.py
# wait for endpoint READY, then:
pip install -r app/requirements.txt
python app/app.py
# open http://localhost:7860
```
