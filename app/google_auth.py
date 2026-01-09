import streamlit as st
from google_auth_oauthlib.flow import Flow
import os

# Scopes required for the app:
# - documents: to create and edit Google Docs
# - drive.file: to view/manage files created by this app
SCOPES = [
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/drive.file'
]

def get_auth_flow():
    """Returns a Flow object configured from Streamlit secrets."""
    # Detect environment: Cloud or Local
    if os.getenv('STREAMLIT_SHARING_MODE'):
         # In Streamlit Cloud, specific URL is required. 
         # Best practice: User puts the production URL in secrets, or we construct it.
         # For simplicity, let's ask user to put it in secrets or defaulting to a placeholder that needs changing.
         # Actually, better: allow override via secrets, default to localhost for dev.
         redirect_uri = st.secrets.get("redirect_url", "http://localhost:8501")
    else:
         redirect_uri = "http://localhost:8501"

    # Robust Secret Access
    if "client" not in st.secrets:
        st.error("Missing [client] section in secrets.toml (or Streamlit Cloud Secrets). Please check DEPLOYMENT.md.")
        st.stop()

    client_config = {
        "web": {
            "client_id": st.secrets["client"]["client_id"],
            "client_secret": st.secrets["client"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    return flow

def login():
    """Generates and returns the authorization URL."""
    flow = get_auth_flow()
    # prompt='consent' ensures we always get a refresh token if needed, 
    # and forces the user to see the consent screen.
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url

def auth_code_to_creds(code):
    """Exchanges the authorization code for credentials."""
    flow = get_auth_flow()
    flow.fetch_token(code=code)
    return flow.credentials
