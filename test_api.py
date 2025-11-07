import requests
import json
url = "http://127.0.0.1:5000/query"

my_query = input("Enter ur query : ")

print(f"Sending query to server: '{my_query}'")
payload = {
    "query": my_query
}

try:
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("--- API Response ---")
        
        # Print the code Gemini generated
        # print(f"Generated Code:\n{data['generated_code']}\n")
        
        if data['error']:
            print(f"Error from server:\n{data['error']}")
        else:
            print(f"Output:\n{data['output']}")
    else:
        print(f"Error: Server returned status code {response.status_code}")
        print(f"Details: {response.text}")

except requests.exceptions.ConnectionError:
    print("\n--- CONNECTION ERROR ---")
    print("Error: Could not connect to the API server.")
    print("Are you sure 'python api_flask.py' is running in another terminal?")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 