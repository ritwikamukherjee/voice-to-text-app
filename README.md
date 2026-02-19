# Voice-to-Text App

Whisper transcription on Databricks: clone the repo → one-time setup (notebook) → deploy and run the Gradio app as a Databricks App. No bundles, just code. No catalog, schema, or workspace names are hardcoded — you configure them.

---

## Get the code

Clone the repo into your Databricks workspace (e.g. via **Repos** → connect this repo) or clone locally and upload the folder. Do not rely on manually uploading files; use **git clone** (or Repos) so you have the full project and can pull updates.

```bash
git clone https://github.com/ritwikamukherjee/voice-to-text-app.git
```

In Databricks: **Repos** → **Add repo** → use the repo URL, or clone into a workspace path.

---

## Configuration (required before running)

You must set **CATALOG** and **SCHEMA** (and optionally **ENDPOINT_NAME**) before running setup or the app. Two ways:

**Option 1 – Edit `config.py`**

Open **config.py** and set `CATALOG`, `SCHEMA`, and optionally `ENDPOINT_NAME`.

**Option 2 – Environment variables (recommended in the notebook)**

Set **CATALOG** and **SCHEMA** (and optionally **ENDPOINT_NAME**) in your environment, or **in the notebook itself using the widgets** in **Setup.ipynb**. The setup notebook has **Catalog** and **Schema** text widgets that set these for you before running register_model and create_endpoint — no need to edit config.py if you use the notebook.

If you run `register_model.py` or `create_endpoint.py` without setting these (and without using the notebook widgets), the scripts exit with a clear message asking you to configure them.

---

## One-time setup (run the notebook)

1. **Open Setup.ipynb** in the cloned repo (in your workspace or locally).
2. **Configure in the notebook:**
   - Enter your Unity Catalog **Catalog** and **Schema** in the **widgets** at the top of the first code cell.
   - Set **REPO_PATH** in that same cell to the path where the repo lives (e.g. `/Workspace/Users/<your-email>/voice-to-text-app` or your Repos path).
3. **Run the first cell** so the widgets and path are applied.
4. **Attach a cluster** and run the rest of the notebook in order:
   - **1. Register Whisper model** — run the cell; wait until you see `Registered: ... version N`.
   - Wait for the model to be **READY** in **Catalog** (your catalog → schema → `whisper_base_transcription`).
   - **2. Create serving endpoint** — run the cell; wait **10–15 minutes** until the endpoint is **READY** under **Serving**.

The configuration (catalog, schema) and flow are aligned: use the widgets in the notebook, then run the two setup steps in order.

---

## Run the app (Databricks App)

When the endpoint is **READY**, run the Gradio UI as a **Databricks App**. This follows the [Databricks Apps get-started guide](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started).

1. In your workspace, click **+ New** → **App** (or go to **Apps** → **Create app**).
2. **Source:** point the app at the **repo root** (the cloned folder that contains `app/` and `config.py`). Use the workspace path or Repos path where you cloned the repo.
3. **Start command:** `python app/app.py`
4. Set **Requirements** to use **app/requirements.txt** if the UI lets you specify a path; otherwise the app runtime will use the root **requirements.txt**.
5. Create/install the app. It will start and show an **app URL** on the Overview page.
6. Click the URL to open the app. Grant the app **Can query** on the **whisper-transcription** serving endpoint (Serving → endpoint → Permissions) so it can call the model.

To re-deploy after code changes, use the **Deploy** action (or the deploy command shown on the app Overview page). For local development and debugging, you can use `databricks apps run-local` from the app directory; see the [get-started guide](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started) for sync and run-local steps.

Set **ENDPOINT_NAME** in config or env if you used a different endpoint name.

---

## Run locally (optional)

For local development or debugging, use the [Databricks Apps get-started guide](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started): set up your environment, then from the app directory run `databricks apps run-local --prepare-environment --debug` (or `python app/app.py` with **CATALOG** and **SCHEMA** set in config or env). Re-deploy to the workspace using the deploy command from the app Overview page.
