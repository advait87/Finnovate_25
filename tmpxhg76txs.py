
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
pd.options.display.float_format = '{:,.2f}'.format

try:
    # *** This is your new line, loading the Excel file directly ***
    data = pd.read_excel("Trial_Balance.xlsx", header=2, usecols="A:G")
    
    # --- This is the code from Gemini (now correctly indented) ---
    print(data['Amount'].sum())
    # ----------------------------------------------------------

except FileNotFoundError:
    print("Error: Could not find shared data file 'Trial_Balance.xlsx'.")
except Exception as e:
    print(f"An error occurred: {e}")
