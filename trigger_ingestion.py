#!/usr/bin/env python3
"""
Script to trigger the ingestion of book content into Qdrant via the admin endpoint
"""

import requests
import time
import json

def test_server_health():
    """Test if the server is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        return response.status_code == 200
    except:
        return False

def trigger_ingestion():
    """Trigger the ingestion endpoint"""
    # First try with a default admin key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "your-admin-key"  # This should be set in your environment
    }

    try:
        response = requests.post(
            "http://localhost:8000/admin/ingest",
            headers=headers,
            timeout=300  # 5 minute timeout for ingestion
        )
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error calling ingestion endpoint: {e}")
        # Try without API key to see if it's an auth issue
        try:
            response = requests.post(
                "http://localhost:8000/admin/ingest",
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            print(f"Response without API key: {response.status_code}, {response.text}")
            return response
        except requests.exceptions.RequestException as e2:
            print(f"Error without API key too: {e2}")
            return None

def main():
    print("Waiting for server to start...")

    # Wait for server to be ready
    max_wait_time = 60  # Wait up to 60 seconds
    wait_interval = 2
    elapsed = 0

    while elapsed < max_wait_time:
        if test_server_health():
            print("✅ Server is running!")
            break
        else:
            print(f"⏳ Waiting for server... ({elapsed}/{max_wait_time}s)")
            time.sleep(wait_interval)
            elapsed += wait_interval
    else:
        print("❌ Server did not start within the expected time")
        return False

    print("Triggering content ingestion...")
    response = trigger_ingestion()

    if response:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            print("✅ Ingestion triggered successfully!")
        else:
            print(f"❌ Ingestion failed with status {response.status_code}")
            # Try to get admin key error
            if response.status_code == 401:
                print("Authentication required - check your ADMIN_API_KEY environment variable")
    else:
        print("❌ Failed to trigger ingestion")
        return False

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Content ingestion process completed!")
        print("The book content should now be stored in Qdrant with all required fields.")
    else:
        print("\n❌ Content ingestion process failed.")