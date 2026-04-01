#!/usr/bin/env python
import requests
import json

# API endpoint for login
login_url = "http://localhost:8000/api/v1/auth/login/access-token"

# Admin credentials
credentials = {
    "username": "admin@forestfire.com",  # Backend expects username field for email
    "password": "adminpassword",
}

# Make the login request
try:
    print("Attempting to login with admin credentials...")
    response = requests.post(
        login_url, 
        data=credentials,  # Use data instead of json for form data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Print response status and content
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Login successful!")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Login failed. Response: {response.text}")
        
except Exception as e:
    print(f"Error during login request: {e}") 