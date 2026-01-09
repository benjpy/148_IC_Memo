import io
import pandas as pd
from pypdf import PdfReader
from PIL import Image

def read_pdf(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"[Error reading PDF: {e}]"

def read_excel(file_bytes):
    try:
        # Check if it's CSV or Excel based on content or try both?
        # Streamlit file uploader gives name, but here we just get bytes usually.
        # We need the filename to know the type or try-except.
        # For simplicity, assuming xlsx for now if not csv.
        # Ideally we pass file object directly from streamlit.
        pass
    except Exception:
        pass
    return ""

def process_uploaded_file(uploaded_file):
    """
    Dispatcher for processing different file types from Streamlit.
    """
    file_type = uploaded_file.name.split('.')[-1].lower()
    content = ""
    
    try:
        if file_type == 'pdf':
            content = read_pdf(uploaded_file.getvalue())
        elif file_type in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            content = df.to_string()
        elif file_type == 'csv':
            df = pd.read_csv(uploaded_file)
            content = df.to_string()
        elif file_type in ['txt', 'md']:
             content = uploaded_file.getvalue().decode("utf-8")
        elif file_type in ['png', 'jpg', 'jpeg']:
            # For images, we return the PIL Image object to be sent to Gemini directly
            image = Image.open(uploaded_file)
            return {"type": "image", "content": image, "name": uploaded_file.name}
        else:
            return f"[Unsupported file type: {file_type}]"
    except Exception as e:
        return f"[Error processing file {uploaded_file.name}: {e}]"

    return {"type": "text", "content": f"--- File: {uploaded_file.name} ---\n{content}\n", "name": uploaded_file.name}
