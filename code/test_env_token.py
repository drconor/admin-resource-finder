#!/usr/bin/env python3
"""Test script to verify API token is accessible from environment variables."""

import os
import sys

def check_api_token():
    """Check if API token is available in environment."""
    token_var_names = [
        "CUSTOM_KEY",
        "CODE_OCEAN_API_TOKEN",
        "API_TOKEN",
        "CO_API_TOKEN",
        "CODEOCEAN_API_TOKEN"
    ]
    
    print("Checking for API token in environment variables...\n")
    
    found = False
    for var_name in token_var_names:
        value = os.environ.get(var_name)
        if value:
            # Mask the token for security
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✓ {var_name}: Found ({masked})")
            found = True
        else:
            print(f"✗ {var_name}: Not set")
    
    print()
    
    if found:
        print("SUCCESS: API token is accessible from environment variables!")
        print("The capsule code will be able to authenticate with the Code Ocean API.")
        return 0
    else:
        print("WARNING: No API token found in environment variables.")
        print("\nTo fix this:")
        print("1. Go to Capsule > Environment > Environment Variables")
        print("2. Add a secret variable named 'CUSTOM_KEY' or 'API_TOKEN'")
        print("3. Enter your API token value")
        print("4. Re-run this test")
        return 1

if __name__ == "__main__":
    sys.exit(check_api_token())
