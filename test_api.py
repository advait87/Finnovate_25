import requests
import json
url = "http://127.0.0.1:5000/query"

my_query = "amount of 10th gl"

print(f"Sending query to server: '{my_query}'")
payload = {
    "query": my_query
}
try:
    # Send the POST request with your JSON payload
    response = requests.post(url, json=payload)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Success: Print the plain text response directly
        print(response.text.strip())
        
    else:
        # Error: The server also sends plain text for errors
        print(f"--- Server Error (HTTP {response.status_code}) ---")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("\n--- CONNECTION ERROR ---")
    print("Error: Could not connect to the API server.")
    print("Are you sure 'python server.py' is running in another terminal?")
except Exception as e:
    print(f"An unexpected error occurred: {e}")