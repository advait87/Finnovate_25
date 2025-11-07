import pandas as pd
import google.generativeai as genai
import subprocess
import tempfile
import os
import json
import textwrap
from flask import Flask, request, jsonify, abort
import atexit

# --- 1. Configuration ---

# Make sure to set this in your environment or paste it here
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
except KeyError:
    print("Error: GEMINI_API_KEY environment variable not set.")
    # You can paste it here directly for testing:
    GEMINI_API_KEY = "AIzaSyCUtaj7lk7yCQ88H3w-zpwcI9vExE7m7Qg" 
    
   

# Define your data file and columns
EXCEL_FILE = "Trial_Balance.xlsx"
DATA_COLUMNS = "[GL, GL Name, Gr GL, Gr GL Name, Amount, FS Grouping Main Head, FS Grouping Main Sub Head]"

# This is the "brain" of the AI
# This is the "brain" of the AI
# This is the "brain" of the AI
# This is the "brain" of the AI
# This is the "brain" of the AI
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
def execute_code(code: str) -> tuple[str, str]:
    """Wraps code, saves to temp file, and runs it in a subprocess."""
    
    indented_code = textwrap.indent(code, '    ')

    # This script_content now loads the Excel file directly
    script_content = f"""
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.display.float_format = '{{:,.2f}}'.format

try:
    # *** This is your new line, loading the Excel file directly ***
    data = pd.read_excel("{EXCEL_FILE}", header=2, usecols="A:G")
    
    # --- This is the code from Gemini (now correctly indented) ---
{indented_code}
    # ----------------------------------------------------------

except FileNotFoundError:
    print("Error: Could not find shared data file '{EXCEL_FILE}'.")
except Exception as e:
    print(f"An error occurred: {{e}}")
"""
    
    try:
        # This will create and save the temp .py file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, dir=".") as f:
            f.write(script_content)
            temp_file_name = f.name
        
        print(f"Running temp file: {temp_file_name}")

        result = subprocess.run(
            ['python', temp_file_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        return result.stdout, result.stderr
        
    finally:
        # We are still keeping the temp .py files for debugging
        # if 'temp_file_name' in locals() and os.path.exists(temp_file_name):
        #     os.remove(temp_file_name)
        pass

# --- 4. API Endpoint ---

@app.route("/query", methods=["POST"])
def handle_query():
    """
    The main API endpoint. Takes a natural language query
    and returns the result from the DataFrame.
    """
    # Get the JSON data from the request
    data = request.get_json()
    if not data or 'query' not in data:
        abort(400, description="Invalid request: JSON body with 'query' key is required.")
        
    user_query = data['query']
    if not user_query:
        abort(400, description="Invalid request: 'query' cannot be empty.")
        
    try:
        # Step 1: Get code from Gemini
        generated_code = get_gemini_code(user_query)
        if not generated_code:
            # Return a 500 internal server error
            return jsonify({"error": "Gemini failed to generate code."}), 500
            
        # Step 2: Run code safely
        stdout, stderr = execute_code(generated_code)
        
        # Step 3: Return the result
        return jsonify({
            "output": stdout,
            "error": stderr if stderr else None,
            "generated_code": generated_code
        })
        
    except Exception as e:
        # Return a 500 internal server error
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500

# --- 5. Run the server ---
if __name__ == "__main__":
    setup_server() # Run the setup
    print(f"Starting Flask server on [http://127.0.0.1:5000](http://127.0.0.1:5000)")
    app.run(debug=True, use_reloader=False, port=5000, host="127.0.0.1")