import pandas as pd
import google.generativeai as genai
import subprocess
import tempfile
import os
import json
import textwrap
import datetime
from flask import Flask, request, jsonify, abort
import atexit

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")

    GEMINI_API_KEY = "AIzaSyCUtaj7lk7yCQ88H3w-zpwcI9vExE7m7Qg" 
    
   

EXCEL_FILE = "Trial_Balance.xlsx"
DATA_COLUMNS = "[GL, GL Name, Gr GL, Gr GL Name, Amount, FS Grouping Main Head, FS Grouping Main Sub Head]"
TEMP_FILE_DIR = os.path.join(SCRIPT_DIR, "Logs")

SYSTEM_PROMPT = f"""
You are an expert Python Pandas code assistant.
A pandas DataFrame named `data` has already been loaded from the Excel file '{EXCEL_FILE}' using pd.read_excel(..., header=2, usecols="A:G").

The DataFrame has the following columns:
{DATA_COLUMNS}

---
Here are some examples of the data in each column to help you verify:
- `GL`: [11100110, 11100200, 11100400, 11200010]
- `GL Name`: ["Inventory-Raw Material-Domestic", "Capital Inventory-Domestic", "Inventory-Stores & Spares-Domestic", "Business Partner-Loan"]
- `FS Grouping Main Head`: ["Non-Current Assets", "Current Assets", "Current Liabilities"]
- `FS Grouping Main Sub Head`: ["Capital work-in-progress", "Inventories", "Financial Liabilities - Other financial liabil..."]
---

Your task is to generate *ONLY* the single block of Python code needed to answer the user's question.
- The code *MUST* include a `print()` statement to display the final result.

**RULES:**
1.  **CONTEXT AWARENESS:** You *MUST* use the data examples above to decide which column to filter. For example, if the user asks for "Current Assets", you know to filter the `FS Grouping Main Head` column. If they ask for "Inventories", you filter the `FS Grouping Main Sub Head` column.
2.  **SINGLE VALUE:** If the result is a single value (e.g., one number, one name), use `.values[0]` or `.iloc[0]` to print **only the value** itself, not the index or dtype. If the filter might be empty, you must first check if the dataframe is empty before getting the value.
3.  **CASE-INSENSITIVE:** When filtering on text columns (like `GL Name` or `FS Grouping Main Head`), always use `.str.lower()` on the DataFrame column to make the comparison case-insensitive.
4.  **FULL DATAFRAME:** If the result is multiple rows, print the full DataFrame.
5.  **NO MARKDOWN:** Do NOT include markdown (like ```python) or any explanation.
6.  **NO LOAD CODE:** Do NOT include the code to load the data; it is already loaded.

---
Example Request 1 (Single Value):
what is the amount of gl 11100110

Example Response 1:
print(data[data['GL'] == 11100110]['Amount'].values[0])

Example Request 2 (Context + Case-Insensitive):
show me all current assets

Example Response 2 (Based on the new rules):
print(data[data['FS Grouping Main Head'].str.lower() == 'current assets'])

Example Request 3 (Context + Case-Insensitive + Single Value):
give me the first gl id in which there will be the first current assets occuring

Example Response 3 (Based on the new rules):
df_filtered = data[data['FS Grouping Main Head'].str.lower() == 'current assets']
if not df_filtered.empty:
    print(df_filtered['GL'].iloc[0])
else:
    print("No matching 'Current Assets' found.")
"""
# --- 2. Initialize Flask, AI Model, and Load Data ---

app = Flask(__name__)
model = None
def setup_server():
    """
    This function runs once before the server starts.
    It checks if the Excel file exists and sets up the AI.
    """
    global model
    print("Server starting up...")
    
    # Configure Gemini
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        model.generate_content("test")
        print("Gemini model configured and tested.")
    except Exception as e:
        print(f"FATAL ERROR: Could not configure Gemini: {e}")
        exit()

    # Load and cache data
    try:
        # We just check if the file exists. We don't load it here.
        if not os.path.exists(EXCEL_FILE):
            raise FileNotFoundError(f"File not found: {EXCEL_FILE}")
        
        print(f"Verified that data file '{EXCEL_FILE}' exists.")

    except FileNotFoundError:
        print(f"FATAL ERROR: Could not find the file {EXCEL_FILE}")
        exit()
    except Exception as e:
        print(f"FATAL ERROR: Error checking data file: {e}")
        exit()
    try:
        if not os.path.exists(TEMP_FILE_DIR):
            os.makedirs(TEMP_FILE_DIR)
            print(f"Created query log directory: {TEMP_FILE_DIR}")
        else:
            print(f"Query log directory found: {TEMP_FILE_DIR}")
    except Exception as e:
        print(f"FATAL ERROR: Could not create directory {TEMP_FILE_DIR}: {e}")
        exit()
    
    
        
    @app.teardown_appcontext
    def cleanup(exception=None):
        pass

    # Register cleanup function to run on exit
    @app.teardown_appcontext
    def cleanup(exception=None):
        pass # Using 'atexit' is more reliable for file cleanup


def cleanup_cache():
    """Runs when the server is stopped (e.g., Ctrl+C)."""
    print("\nServer shutting down. Goodbye!")
    
atexit.register(cleanup_cache)
rn

# --- 3. Helper Functions (Your original logic) ---

def get_gemini_code(user_query: str) -> str:
    """Sends the query to Gemini and returns the code string."""
    if not model:
        raise Exception("Gemini model is not initialized.")
    try:
        full_prompt = SYSTEM_PROMPT + "\nUser Request:\n" + user_query
        response = model.generate_content(full_prompt)
        
        code = response.text.strip()
        code = code.replace("```python", "").replace("```", "").strip()
        return code
        
    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        return ""

def execute_code(code: str, user_query: str) -> tuple[str, str]:
    """Wraps code, saves to a timestamped file, and runs it."""
    
    indented_code = textwrap.indent(code, '    ')

    # IMPORTANT: We must escape backslashes in the file paths for the f-string
    # This turns 'C:\Users...' into 'C:\\Users...' for the Python script
    excel_file_path_for_script = EXCEL_FILE.replace("\\", "\\\\")

    script_content = f"""
# --- USER QUERY ---
# {user_query}
# --------------------

import pandas as pd
import warnings
import os
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.display.float_format = '{{:,.2f}}'.format

try:
    # Use the full, escaped path to the Excel file
    data = pd.read_excel(r"{excel_file_path_for_script}", header=2, usecols="A:G")
    
    # --- This is the code from Gemini (now correctly indented) ---
{indented_code}
    # ----------------------------------------------------------

except FileNotFoundError:
    print("Error: Could not find shared data file '{EXCEL_FILE}'.")
except Exception as e:
    print(f"An error occurred: {{e}}")
"""
    
    # 1. Get the current time
    now = datetime.datetime.now()
    
    # 2. Create the short filename (with microseconds)
    short_filename = now.strftime("%Y.%m.%d_%H.%M.%S.py")
    
    # 3. Join with the 'Logs' directory (absolute path)
    temp_file_name = os.path.join(TEMP_FILE_DIR, short_filename)
        
    try:
        # 4. Create and write to that absolute path
        with open(temp_file_name, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        print(f"Running temp file: {temp_file_name}")

        result = subprocess.run(
            ['python', temp_file_name],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8'
        )
        
        return result.stdout, result.stderr
        
    finally:
        # We are keeping the temp .py files for logging
        pass
# --- 4. API Endpoint ---

@app.route("/query", methods=["POST"])
@app.route("/query", methods=["GET", "POST"])  # <-- Now accepts GET and POST
def handle_query():
    """
    The main API endpoint. Takes a natural language query
    and returns the result from the DataFrame.
    """
    user_query = None
    
    if request.method == "POST":
        data = request.get_json()
        if not data or 'query' not in data:
            abort(400, description="Invalid POST: JSON body with 'query' key is required.")
        user_query = data['query']
        
    elif request.method == "GET":
        user_query = request.args.get("query")
        if not user_query:
            abort(400, description="Invalid GET: URL parameter 'query' is required. (e.g., /query?query=your question)")

    if not user_query:
        abort(400, description="Invalid request: 'query' cannot be empty.")
        
    try:
        generated_code = get_gemini_code(user_query)
        if not generated_code:
            return "Error: Gemini failed to generate code.", 500
            
        # *** CHANGE 1: Pass the user_query to execute_code ***
        stdout, stderr = execute_code(generated_code, user_query)
        
        # *** CHANGE 2: Return plain text, not JSON ***
        if stderr:
            # If there was an error in the script, return it
            return f"An error occurred:\n{stderr}", 500
        else:
            # If successful, return ONLY the clean output
            return stdout.strip(), 200
        
    except Exception as e:
        return f"An internal server error occurred: {str(e)}", 500
# --- 5. Run the server ---
if __name__ == "__main__":
    setup_server() # Run the setup
    print(f"Starting Flask server on [http://127.0.0.1:5000](http://127.0.0.1:5000)")
    app.run(debug=True, use_reloader=False, port=5000, host="127.0.0.1")