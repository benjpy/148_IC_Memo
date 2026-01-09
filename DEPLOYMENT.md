# Deployment Guide: IC Memo Generator

This application is ready for deployment on [Streamlit Cloud](https://streamlit.io/cloud).

## 1. GitHub Setup

1.  **Initialize Git** (if not done):
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```
2.  **Push to GitHub**:
    - Create a new repository on GitHub.
    - Follow the instructions to push your local code to the new repository.

## 2. Streamlit Cloud Setup

1.  **New App**: Go to Streamlit Cloud and click "New app".
2.  **Connect Repo**: Select your GitHub repository.
3.  **Main File**: Ensure `streamlit_app.py` is selected.
4.  **Python Version**: Recommended `3.9` or `3.10`.

## 3. Configuration (Secrets)

**CRITICAL**: You must set your secrets in the Streamlit Cloud dashboard.
Go to **Advanced Settings** -> **Secrets** and paste the content below:

```toml
[client]
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
```

**Also add your Gemini API Key:**

```toml
GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"
```

*(Note: Streamlit Cloud reads `secrets.toml` but treats top-level keys as environment variables if formatted that way, or you can access them via `st.secrets`)*.

For this app we access `os.getenv("GOOGLE_API_KEY")`. In Streamlit Cloud, you can put it in the secrets box like `GOOGLE_API_KEY = "..."` and it will be accessible via `st.secrets` OR environment variables depending on platform version, but safe bet is:

**Secrets Box Content:**
```toml
GOOGLE_API_KEY = "ai-..."

[client]
client_id = "..."
client_secret = "..."
```

## 4. Google Cloud Console (OAuth)

1.  **Authorized Redirect URI**:
    - When deployed, your app will have a URL like `https://your-app-name.streamlit.app`.
    - Go to Google Cloud Console > Credentials > Your OAuth Client.
    - **ADD** this new URL to "Authorized Redirect URIs":
      `https://your-app-name.streamlit.app`
      (and potentially `https://your-app-name.streamlit.app/` just in case).
2.  **Test Users**:
    - If in Testing mode, ensure any user logging in is in the "Test users" list.
