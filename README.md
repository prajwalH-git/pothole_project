# Pothole Tracker - Web UI for Local Governance (Flask + Leaflet)

## Run locally
1. Create virtual env:

2. (Optional) Generate big dataset:

3. Import CSV:

# OR


4. Run app:

Open http://127.0.0.1:5000/user

## Deploy to Render
- Push repo to GitHub.
- Create new Web Service on Render, connect repo.
- Set Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Set environment variable `OWM_KEY` in Render for weather API (optional).

