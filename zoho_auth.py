# FILE: zoho_auth.py
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_access_token():
    # Read credentials from environment variables
    REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
    CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
    CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")

    url = "https://accounts.zoho.com.au/oauth/v2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    try:
        res = requests.post(url, data=payload)
        
        # DEBUGGING: This will print exactly what Zoho sends back
        print(f"\n🔑 DEBUG: Zoho Response: {res.json()}") 
        
        res.raise_for_status()
        return res.json()["access_token"]

    except Exception as e:
        print(f"❌ AUTH FAILED: {e}")
        return None