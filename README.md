📄 README: AI-Powered Document Structuring & Data Extraction
This project implements an AI-backed solution to convert unstructured PDF documents into a clean, structured Excel (XLSX) output. It leverages the high-speed inference capabilities of Groq's LLM API and provides a user-friendly interface via Streamlit.

The solution is specifically designed to meet stringent data fidelity requirements, ensuring 100% data capture and selective contextual commenting.

🚀 Key Features
PDF to Excel Transformation: Converts unstructured text into a tabular Key:Value format.
LLM-Driven Structuring: Uses a Large Language Model (currently Llama 3.3 70B) to intelligently identify and structure data relationships without pre-defining keys.
100% Data Fidelity: Strict prompt engineering ensures all original content is captured across the output columns.
Streamlit UI: Provides an easy-to-use web interface for file upload and structured data download.
Pydantic Schema Enforcement: Guarantees reliable, structured JSON output from the LLM, preventing parsing errors.

🛠️ Setup Instructions
Follow these steps to set up and run the application locally.-->

1. File Structure
Ensure your project directory matches this structure:

document-extractor/
├── solutions.py             # Main Streamlit application code
├── requirements.txt         # List of necessary Python libraries
└── .env                     # File for storing your Groq API Key

2. Install Dependencies
You need Python 3.12 or newer. Install all required libraries using pip:
pip install -r requirements.txt

3. Configure API Key
The application requires a Groq API Key.

Sign up for an API key at [GroqCloud].
Create a file named .env in the root of your project directory (document-extractor/) and add your key:

4. Code snippet

# .env file content
GROQ_API_KEY='your_groq_api_key_here'


🖥️ Usage Instructions
Once setup is complete, you can run the application.

1. Run the Streamlit Application
Execute the following command in your terminal from the project's root directory:
streamlit run app.py
This command will automatically open the application in your default web browser (usually at http://localhost:8501).

2. Process the Document
Follow the steps outlined in the web interface:

Upload Input Document (Step 1): Click the file uploader and select your Data Input.pdf file.
Preview Extracted Text (Step 2 - Optional): Click this button to verify that the text extraction from the PDF was successful before engaging the LLM.
Run Data Extraction (LLM) (Step 3): Click the primary button to send the PDF text to the Groq LLM. The LLM will parse, structure, and format the data according to the strict requirements.
Download Output (Step 4): Once processing is complete, a data preview will appear, followed by a Download Expected Output.xlsx button. Click this to download the final structured Excel file.


🧠 Technical Implementation Details
Component	Purpose	Details
LLM Provider	GroqCloud	Used for high-speed, low-latency inference.
Model	llama-3.3-70b-versatile	Chosen for its superior capability in following complex, structured output (JSON) instructions.
Structuring	Pydantic	Defines the rigid DocumentStructure and ExtractedPair schemas to ensure the LLM's output is always valid JSON.
PDF Handling	pypdf	Extracts raw text content from the PDF, which is then fed into the LLM prompt.
Excel Output	openpyxl	Writes the validated JSON data directly into an in-memory XLSX file for download.


⚠️ Troubleshooting
API Key Error: If the sidebar shows "API Status: Disconnected," ensure you have saved your key correctly in the .env file and restarted the Streamlit app.
error: command 'cmake' failed: This indicates a Python version issue. The recommended solution is to use Python 3.12 or a recently supported version to avoid attempting complex source compilation.
"JSON Parsing Error" (Validation Error): This means the LLM deviated from the schema. The strict prompt (especially Requirement 6) is designed to mitigate this, but complex or poorly formatted input PDFs may occasionally confuse the LLM. Re-run the process, or review the PDF input.
