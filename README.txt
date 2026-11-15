# FindIt AI — shareable website

This is a small Streamlit chat website connected to the existing CrewAI deployment.

## Files
- `app.py` — chat interface and CrewAI API connection
- `requirements.txt` — Python packages

## Publish
1. Create a GitHub repository and upload `app.py` and `requirements.txt`.
2. Open Streamlit Community Cloud and create an app from that repository.
3. Set the main file to `app.py`.
4. In the app's Settings → Secrets, add:

```toml
CREWAI_API_URL = "https://findit-ai-62d3c77f-763b-49c7-85b0-4bb70314d-4e9d1cbf.crewai.com"
CREWAI_BEARER_TOKEN = "paste-your-private-token-here"
```

5. Save and reboot the app.

Keep the bearer token in Streamlit Secrets only. Never commit it to GitHub or share it publicly.

The app submits the known FindIt AI input fields to `POST /kickoff` and polls `GET /status/{kickoff_id}` for the result.
