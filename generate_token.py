import os
import sys
from urllib.parse import urlparse, parse_qs
import requests
from dotenv import load_dotenv

# Add project root to path to allow imports from other files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import spotify
except ImportError:
    print("Error: `spotify.py` not found. Make sure this script is in the main project directory.")
    sys.exit(1)

def main():
    """
    A command-line tool to generate a Spotify refresh token.
    """
    load_dotenv()

    # Check if necessary environment variables are set
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    if not client_id or not redirect_uri:
        print("Error: Please set the SPOTIFY_CLIENT_ID and SPOTIFY_REDIRECT_URI variables in your .env file.")
        return

    # 1. Get authorization URL
    auth_url = spotify.get_auth_url()

    print("-" * 60)
    print("Spotify Refresh Token Generator")
    print("-" * 60)
    print("\nStep 1: Copy the following URL and open it in your browser:")
    print("\n" + auth_url + "\n")
    print("Step 2: Log in to Spotify and grant permission to the application.")
    print("Step 3: After authorizing, your browser will redirect to a page that might show a 'not found' error. This is normal.")
    print("   Copy the entire URL from your browser's address bar.")

    # 2. Get the redirected URL from user
    callback_url = input("\nStep 4: Paste the full redirected URL here and press Enter:\n> ")

    # 3. Parse the authorization code from the URL
    try:
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        auth_code = query_params.get("code", [None])[0]

        if not auth_code:
            print("\nError: Could not find 'code' parameter in the URL. Please make sure you copied the correct URL.")
            return

    except Exception:
        print("\nError: You entered an invalid URL.")
        return

    # 4. Exchange the code for tokens
    print("\nAuthorization code received, requesting tokens from Spotify...")
    try:
        token_data = spotify.get_token_data_from_code(auth_code)
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        if not refresh_token:
            print("\nError: Could not retrieve refresh_token from Spotify. There might be an issue with permissions.")
            print("Response from Spotify:", token_data)
            return

        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("Copy the Refresh Token below and paste it into your .env file")
        print("for the MY_SPOTIFY_REFRESH_TOKEN variable.")
        print("-" * 60)
        print(f"\nRefresh Token: {refresh_token}\n")
        print("=" * 60)

    except requests.exceptions.HTTPError as e:
        print(f"\nError: An error occurred while fetching tokens from Spotify (HTTP {e.response.status_code}).")
        print("Response from Spotify:", e.response.json())
        print("\nPlease ensure your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in the .env file are correct.")
        print("Also, verify that the Redirect URI in your Spotify Developer Dashboard matches the one in your .env file.")

if __name__ == "__main__":
    main()
