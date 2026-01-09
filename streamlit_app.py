import streamlit as st
import os
from dotenv import load_dotenv

from app.google_auth import login, auth_code_to_creds
from app.utils import process_uploaded_file
from app.extraction import ExtractionEngine
from app.document_builder import DocumentBuilder
from app.cost_tracker import CostTracker

# Load Environment Variables (API Key for Gemini)
load_dotenv(override=True)

# 1. App Configuration
st.set_page_config(
    page_title="IC Memo Generator (OAuth)",
    page_icon="📄",
    layout="wide"
)

st.title("📄 IC Memo Generator")
st.markdown("Generate V2 Investment Committee Memos from uploaded documents.")

# 2. Authentication Logic
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Check for Auth Code in Query Params (Callback)
if not st.session_state.credentials:
    # Use st.query_params (Streamlit > 1.30)
    query_params = st.query_params
    auth_code = query_params.get("code")
    
    if auth_code:
        try:
            with st.spinner("Authenticating..."):
                creds = auth_code_to_creds(auth_code)
                st.session_state.credentials = creds
            st.success("Authentication Successful! Reloading...")
            # Clear query params to prevent re-execution of auth logic
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Authentication Failed: {e}")
            st.stop()

# 3. Main Interface
if not st.session_state.credentials:
    st.info("Please sign in with your Google Account to create Google Docs.")
    auth_url = login()
    st.link_button("Login with Google", auth_url, type="primary")
    st.stop()
else:
    st.success("✅ Authenticated with Google Docs")

# 4. Application Logic (Only visible if authenticated)
with st.sidebar:
    st.header("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload Pitch Decks, Financials, Memos",
        type=['pdf', 'xlsx', 'xls', 'csv', 'txt', 'md', 'png', 'jpg'],
        accept_multiple_files=True
    )

    st.markdown("---")
    st.markdown("**Configuration**")
    if os.getenv("GOOGLE_API_KEY"):
        st.caption("✅ Gemini API Key detected")
    else:
        st.error("❌ GOOGLE_API_KEY missing in .env")

if st.button("Generate Memo", type="primary", disabled=not uploaded_files):
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("Please set GOOGLE_API_KEY in .env")
        st.stop()
        
    cost_tracker = CostTracker()
    cost_tracker.start_timer()
    
    status_container = st.status("Processing...", expanded=True)
    
    try:
        # Step 1: Process Files
        status_container.write("📂 Processing uploaded files...")
        processed_data = []
        for file in uploaded_files:
            result = process_uploaded_file(file)
            if isinstance(result, str) and result.startswith("[Error"):
                st.error(result)
            else:
                processed_data.append(result)
        
        # Step 2: Extract Info (Gemini)
        status_container.write("🧠 Extracting information with Gemini 2.5 Flash...")
        extractor = ExtractionEngine(
            api_key=os.getenv("GOOGLE_API_KEY"),
            cost_tracker=cost_tracker
        )
        extracted_data = extractor.extract_all(processed_data)
        status_container.write("✅ Extraction complete.")
        
        # Display Data Preview
        st.subheader("Extracted Data")
        st.json(extracted_data)
        
        # Step 3: Create Google Doc
        status_container.write("📝 Creating formatted Google Doc...")
        doc_builder = DocumentBuilder(st.session_state.credentials)
        doc_url = doc_builder.create_memo(extracted_data)
        
        cost_tracker.stop_timer()
        
        # Step 4: Results
        if doc_url.startswith("http"):
            status_container.update(label="Complete!", state="complete", expanded=False)
            st.markdown(f"### 🎉 Memo Created successfully!")
            st.markdown(f"**[Open Google Doc]({doc_url})**")
        else:
            status_container.update(label="Failed", state="error")
            st.error(f"Failed to create document: {doc_url}")
            
        # Stats
        st.markdown("---")
        summary = cost_tracker.get_summary()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Runtime", f"{summary['total_runtime_seconds']:.2f}s")
        col2.metric("Tokens In", f"{summary['total_input_tokens']:,}")
        col3.metric("Tokens Out", f"{summary['total_output_tokens']:,}")
        col4.metric("Est. Cost", f"${summary['total_cost_usd']:.4f}")

    except Exception as e:
        status_container.update(label="Error", state="error")
        st.error(f"An unexpected error occurred: {e}")
