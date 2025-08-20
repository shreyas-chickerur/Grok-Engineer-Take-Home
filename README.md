# Grok SDR (Streamlit, All-Python)

A 4-hour-friendly prototype of a Grok-powered SDR: lead qualification, personalized outreach, and lightweight evals — all in Streamlit with an SQLite backend.

## Quickstart (Local)
```bash
# 1) Python env
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2) Set your Grok key
export GROK_API_KEY=...   # or put in .env

# 3) Run
streamlit run app.py
```

Open http://localhost:8501

## Docker
```bash
# Build + run
docker compose-up --build
```

## Environment
- `GROK_API_KEY` – your API key
- `GROK_API_URL` – completion/chat endpoint (defaults to a placeholder)
- `GROK_MODEL` – model name (defaults to `grok-2`)
- `DB_PATH` – SQLite location (defaults to `./data/app.db`)

## Features
- Lead CRUD (SQLite)
- One-click **Qualify** (score + tags)
- **Generate Outreach** (personalized email/DM)
- **Activity Log** for each lead
- Lightweight **Evals** tab for prompt iterations
- Export leads to CSV

## Project Structure
- `app.py` – Streamlit UI + handlers
- `db.py` – SQLAlchemy models + simple repository
- `grok_client.py` – Grok API wrapper (+ dry-run)
- `prompts.py` – prompt templates
- `evals.py` – tiny evaluation harness


```
