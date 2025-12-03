import os
import io
import json
from groq import Groq
from pypdf import PdfReader
from pydantic import BaseModel, Field
from openpyxl import Workbook
import streamlit as st
from dotenv import load_dotenv

# --- Configuration & Setup ---
load_dotenv() # Load environment variables from .env file

# NEW RECOMMENDED MODEL for robust JSON extraction (replacing deprecated Mixtral)
# Llama 3.3 70B is chosen for its strong instruction following and complex task capability.
LLM_MODEL = "llama-3.3-70b-versatile" 

# Groq Client Initialization
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = None
if GROQ_API_KEY:
    try:
        # Note: Groq is compatible with the structuredOutputs setting for reliable JSON
        client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        st.error(f"Error initializing Groq client: {e}")
        
# --- Pydantic Data Model ---

class ExtractedPair(BaseModel):
    """Represents a single row of data for the Excel output."""
    Key: str = Field(description="The determined key/label for the piece of information, decided by the LLM.")
    Value: str = Field(description="The raw, exact value associated with the Key, preserving original language.")
    Contextual_Comment: str = Field(description="A note pulled directly from the PDF content that provides context for the pair, or is left empty if Key/Value is sufficient.")

class DocumentStructure(BaseModel):
    """The root model for the structured document output."""
    # The key 'extracted_data' MUST match this field name exactly.
    extracted_data: list[ExtractedPair] = Field(description="A list containing all key:value pairs and their contextual comments extracted from the entire document.")

# --- Core Functions ---

@st.cache_data
def read_pdf_text(uploaded_file: io.BytesIO) -> str:
    """Reads all text content from an uploaded PDF file."""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for i, page in enumerate(reader.pages):
            text += f"\n--- Page {i+1} ---\n"
            # Attempt to extract text. Use conditional formatting if needed.
            page_text = page.extract_text()
            text += page_text if page_text else "(No readable text on this page)"
        return text.strip()
    except Exception as e:
        st.error(f"An error occurred while reading the PDF: {e}")
        return ""

def generate_extraction_prompt(document_text: str) -> str:
    """Creates the detailed system prompt for the LLM with strict schema enforcement."""
    
    return f"""
    You are an advanced AI Data Structuring and Extraction Engine. Your task is to transform the provided
    unstructured document text into a structured JSON format following the exact Pydantic schema provided.

    ## STRICT REQUIREMENTS:
    1.  **100% Capture:** You MUST ensure ALL content from the document is captured across the 'Key', 'Value', and 'Contextual_Comment' fields. Nothing is to be lost, summarized, or omitted.
    2.  **Unstructured to Tabular:** Convert the document's content into a series of logical Key:Value pairs.
    3.  **Key Determination:** DO NOT pre-define the keys. Determine the most appropriate, concise, and logical 'Key'.
    4.  **Value Fidelity:** The 'Value' must be the **exact, original wording/phrasing** from the document.
    5.  **Contextual Comments (CRITICAL CHANGE for Fidelity):**
        * The 'Contextual_Comment' field MUST contain **additional, related text pulled directly from the source PDF** that adds necessary context or is supplementary to the Key/Value pair.
        * **If the Key and Value fields already capture the entire logical sentence or phrase, the 'Contextual_Comment' field MUST be left EMPTY ("")** to strictly adhere to the "Preserve Original Language" rule and avoid redundant output.
    6.  **Schema Enforcement (CRITICAL):** The final JSON object MUST have a **single top-level key** named **'extracted_data'**. DO NOT categorize the data into custom keys like 'Personal_Details' or 'Sections'.

    ## EXAMPLE OUTPUT FORMAT:
    // This example is for structure only. Content must reflect the input PDF.
    {{
        "extracted_data": [
            {{
                "Key": "Assignment Title",
                "Value": "AI-Powered Document Structuring & Data Extraction Task",
                "Contextual_Comment": "" // Example of an empty comment
            }},
            {{
                "Key": "Undergraduate GPA Context",
                "Value": "8.7",
                "Contextual_Comment": "On a 10-point scale." // Example of a required context
            }}
        ]
    }}

    ## DOCUMENT TEXT TO BE PROCESSED:
    ---
    {document_text}
    ---
    """

def extract_data_with_llm(document_text: str) -> list[ExtractedPair] | None:
    """Calls the Groq API to perform the structured data extraction."""
    
    system_prompt = generate_extraction_prompt(document_text)
    
    try:
        with st.spinner(f"🚀 Processing document with Groq LLM ({LLM_MODEL})..."):
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Process the provided document text and return the structured JSON output adhering strictly to the Pydantic schema."}
                ],
                model=LLM_MODEL,
                response_format={"type": "json_object"},
                temperature=0.0
            )
        
        json_string = chat_completion.choices[0].message.content
        data_model = DocumentStructure.model_validate_json(json_string)
        
        return data_model.extracted_data
        
    except Exception as e:
        st.error(f"❌ An error occurred during LLM API call or JSON parsing. Details: {e}")
        st.caption("The LLM might have returned a JSON that violated the strict 'extracted_data' list structure. Review the LLM logs if possible.")
        return None

def create_excel_bytes(extracted_data: list[ExtractedPair]) -> bytes:
    """Creates an Excel file in memory (BytesIO) and returns the bytes."""
    wb = Workbook()
    ws = wb.active
    
    # Set headers
    headers = ["Key", "Value", "Contextual_Comment"]
    ws.append(headers)
    
    # Write data rows
    for item in extracted_data:
        # Using .model_dump() for dictionary conversion
        row = [item.Key, item.Value, item.Contextual_Comment]
        ws.append(row)
        
    # Save to a BytesIO object
    excel_stream = io.BytesIO()
    wb.save(excel_stream)
    excel_bytes = excel_stream.getvalue()
    
    return excel_bytes

# --- Streamlit UI ---

def main():
    st.set_page_config(page_title="AI Document Structuring Tool", layout="wide")
    st.title("📄 AI-Powered Document Structuring & Data Extraction")
    st.markdown("Automating the conversion of unstructured PDF text into a structured Excel table using Groq's high-speed LLMs.")

    # --- Sidebar for Status and Settings ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        if client:
            st.success("API Status: Connected to GroqCloud")
            st.info(f"LLM Model: **{LLM_MODEL}** (Selected for high structured output fidelity)")
        else:
            st.error("API Status: Disconnected (Key Missing)")
            st.warning("Please set your `GROQ_API_KEY` environment variable.")
        st.markdown("---")
        st.markdown(f"**Note:** The previous `mixtral-8x7b-32768` model has been officially decommissioned. We use **{LLM_MODEL}** as the replacement.")

    if client is None:
        st.warning("""
            **Application Disabled:** Cannot connect to the LLM. 
            Please set your Groq API Key to proceed.
        """)
        return

    # --- Main Application Steps ---

    st.subheader("1. Upload Input Document")
    uploaded_file = st.file_uploader(
        "Upload your 'Data Input.pdf' here:", 
        type=["pdf"], 
        help="The document must be text-readable. No OCR support is built-in for image-only files."
    )

    if uploaded_file is not None:
        st.success(f"File uploaded: **{uploaded_file.name}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("2. 🔍 Preview Extracted Text", use_container_width=True):
                # Read PDF content
                pdf_content = read_pdf_text(uploaded_file)
                if pdf_content:
                    st.session_state['pdf_content'] = pdf_content
                    st.caption("First 500 characters of extracted text (for verification):")
                    st.code(pdf_content[:500] + "...", language="text")
                else:
                    st.error("Could not extract text. Please check the PDF file.")

        with col2:
            # Only enable the run button if content is ready or file is uploaded
            process_button = st.button("3. ⚡ Run Data Extraction (LLM)", type="primary", use_container_width=True, 
                                       disabled='pdf_content' not in st.session_state and uploaded_file is None)
            
        st.markdown("---")

        if process_button:
            # Ensure PDF content is loaded before running
            if 'pdf_content' not in st.session_state or st.session_state['pdf_content'] is None:
                st.session_state['pdf_content'] = read_pdf_text(uploaded_file)
            
            pdf_content = st.session_state['pdf_content']
            
            if not pdf_content:
                st.warning("No content found to process. Please ensure the PDF is uploaded and text extraction is successful.")
                return

            # Extract data using LLM
            structured_data = extract_data_with_llm(pdf_content)

            if structured_data:
                st.subheader("4. Extracted Data Output (Preview)")
                st.success(f"✅ Extraction Successful! **{len(structured_data)}** Key:Value pairs captured.")

                # Display the extracted data in an interactive table
                st.dataframe([d.model_dump() for d in structured_data], use_container_width=True, height=300)

                # Create downloadable Excel
                excel_bytes = create_excel_bytes(structured_data)
                st.download_button(
                    label="⬇️ Download Expected Output.xlsx",
                    data=excel_bytes,
                    file_name="Expected_Output_Structured_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="The output is guaranteed to follow the strict Key, Value, Contextual_Comment structure.",
                    key="download_button"
                )
            
if __name__ == "__main__":
    main()