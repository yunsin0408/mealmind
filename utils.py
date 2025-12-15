import requests
from flask import current_app

def query(payload):
    # We access the config securely using current_app
    api_url = current_app.config['HF_URL']
    api_token = current_app.config['HF_TOKEN']
    
    if not api_token:
        return {"error": "API Token is missing"}

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}