import os
import io
import json
from groq import Groq
from pypdf import PdfReader
from pydantic import BaseModel, Field, ConfigDict
from openpyxl import Workbook
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # Optional: Loads .env if available

LLM_MODEL = "llama-3.3-70b-versatile"


# ---------------------------------------------------------
# Function to initialize Groq client based on sidebar input
# ---------------------------------------------------------
def init_client():
    api_key = st.session_state.get("API_KEY", None)

    if not api_key:
        return None, False

    try:
        client = Groq(api_key=api_key)
        return client, True
    except:
        return None, False


# ---------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------
class ExtractedPair(BaseModel):
    Key: str
    Value: str
    comment: str = Field(alias="Comment")
    model_config = ConfigDict(populate_by_name=True)


class DocumentStructure(BaseModel):
    extracted_data: list[ExtractedPair]


# ---------------------------------------------------------
# PDF Extraction
# ---------------------------------------------------------
@st.cache_data
def read_pdf_text(uploaded_file: io.BytesIO) -> str:
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n--- Page {i+1} ---\n"
            page_text = page.extract_text()
            text += page_text if page_text else "(No readable text on this page)"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""


# ---------------------------------------------------------
# Prompt Creation
# ---------------------------------------------------------
def generate_extraction_prompt(document_text: str) -> str:
    return f"""
    You are an advanced AI Data Structuring and Extraction Engine...

    ## DOCUMENT TEXT:
    ---
    {document_text}
    ---
    """


# ---------------------------------------------------------
# LLM Extraction
# ---------------------------------------------------------
def extract_data_with_llm(client, document_text: str, progress_bar):
    system_prompt = generate_extraction_prompt(document_text)

    try:
        progress_bar.progress(60, text="60% - Sending to Groq LLM...")

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Return structured JSON following schema."}
            ],
            model=LLM_MODEL,
            response_format={"type": "json_object"},
            temperature=0.0
        )

        progress_bar.progress(80, text="80% - Validating JSON...")

        json_string = chat_completion.choices[0].message.content
        data_model = DocumentStructure.model_validate_json(json_string)

        progress_bar.progress(95, text="95% - Success!")

        return data_model.extracted_data

    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ LLM Error: {e}")
        return None


# ---------------------------------------------------------
# Excel File Creator
# ---------------------------------------------------------
def create_excel_bytes(extracted_data, progress_bar):
    progress_bar.progress(98, text="Generating Excel...")

    wb = Workbook()
    ws = wb.active
    ws.append(["Key", "Value", "Comment"])

    for item in extracted_data:
        row = item.model_dump(by_alias=True)
        ws.append([row["Key"], row["Value"], row["Comment"]])

    stream = io.BytesIO()
    wb.save(stream)

    progress_bar.progress(100, text="Done!")
    return stream.getvalue()


# ---------------------------------------------------------
# Streamlit App
# ---------------------------------------------------------
def main():
    st.set_page_config(page_title="AI Document Structuring Tool", layout="wide")
    st.title("📄 AI-Powered Document Structuring & Data Extraction")

    # ------------------ Sidebar ------------------
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.markdown("### 🔑 Enter Your Groq API Key")

        st.text_input(
            label="Groq API Key",
            placeholder="Enter your GROQ_API_KEY here",
            type="password",
            key="API_KEY"
        )

        client, connected = init_client()

        if connected:
            st.success("API Status: Connected")
        else:
            st.error("API Status: Disconnected")
            st.info("Enter your API key to enable the LLM.")

        st.markdown("---")
        st.caption("Using Llama 3.3 for high-fidelity structured extraction.")

    # ------------------ Block UI if no API key ------------------
    if not connected:
        st.warning("Please enter your API key in the sidebar to activate the application.")
        return

    # ------------------ Main UI ------------------
    st.markdown("## ➡️ Process Workflow")

    uploaded_file = st.file_uploader("**Step 1:** Upload PDF file", type=["pdf"])

    if uploaded_file:
        st.success(f"Uploaded: {uploaded_file.name}")

        if 'pdf_content' not in st.session_state:
            st.session_state['pdf_content'] = read_pdf_text(uploaded_file)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("2. 🔍 Preview Extracted Text"):
                st.success("Text extracted successfully.")
                with st.expander("Show Text"):
                    st.code(st.session_state['pdf_content'][:1000] + " ...")

        with col2:
            run_extract = st.button("3. ⚡ Run LLM Extraction", type="primary")

        st.markdown("---")

        if run_extract:
            pdf_text = st.session_state['pdf_content']
            progress = st.progress(10, text="Starting...")

            data = extract_data_with_llm(client, pdf_text, progress)

            if data:
                st.subheader("✅ Extraction Complete")

                excel_bytes = create_excel_bytes(data, progress)
                st.dataframe([d.model_dump(by_alias=True) for d in data])

                st.download_button(
                    "⬇️ Download Excel",
                    excel_bytes,
                    "Structured_Output.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )


if __name__ == "__main__":
    main()
