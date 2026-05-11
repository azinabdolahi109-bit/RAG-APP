import requests

url = "http://localhost:8000/ask"
payload = {"question": "What is the total revenue?"}
try:
    response = requests.post(url, json=payload)
    print(response.status_code)
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
