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

    # Validate required environment variables
    if not all([REFRESH_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("❌ Missing required Zoho credentials in environment variables")
        return None
    
    try:
        res = requests.post(url, data=payload, timeout=10)
        
        # DEBUGGING: Log only status code to avoid exposing sensitive tokens
        print(f"✅ Zoho Auth Status: {res.status_code}")

        res.raise_for_status()
        return res.json()["access_token"]

    except Exception as e:
        print(f"❌ AUTH FAILED: {e}")
        return None