import requests
from flask import current_app

def query(payload):
    api_url = current_app.config['HF_URL']
    api_token = current_app.config['HF_TOKEN']
    
    if not api_token:
        return {"error": "API Token is missing"}

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        # If HF returns a non-2xx status, return the body for debugging
        if not response.ok:
            try:
                return {"error": response.json(), "status_code": response.status_code}
            except Exception:
                return {"error": response.text, "status_code": response.status_code}
        return response.json()
    except Exception as e:
        return {"error": str(e)}