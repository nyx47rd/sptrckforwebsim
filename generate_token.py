import os
import sys
from urllib.parse import urlparse, parse_qs, urlencode
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
    This script specifically uses https://example.com/callback as the redirect URI.
    """
    load_dotenv()

    # Check if necessary environment variables are set
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("Error: Please set the SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET variables in your .env file.")
        return

    # For this script, we always use a fixed, non-functional redirect URI.
    # The user must add this exact URI to their Spotify App settings.
    script_redirect_uri = "https://example.com/callback"

    # 1. Get authorization URL
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": script_redirect_uri,
        "scope": spotify.SCOPES,
    }
    auth_url = f"{spotify.SPOTIFY_AUTH_URL}?{urlencode(params)}"

    print("-" * 60)
    print("Spotify Refresh Token Generator")
    print("-" * 60)
    print("\nStep 1: Go to your Spotify Dashboard and add the following Redirect URI:")
    print(f"   {script_redirect_uri}")
    print("\nStep 2: Open the following URL in your browser:")
    print("\n" + auth_url + "\n")
    print("Step 3: Log in to Spotify and grant permission to the application.")
    print("Step 4: After authorizing, your browser will redirect to an 'example.com' page that doesn't exist. This is normal.")
    print("   Copy the entire URL from your browser's address bar.")

    # 2. Get the redirected URL from user
    callback_url = input("\nStep 5: Paste the full redirected URL here and press Enter:\n> ")

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
        # We need to call the token exchange logic directly here
        auth_header = base64.b64encode(
            f"{client_id}:{client_secret}".encode("ascii")
        ).decode("ascii")

        response = requests.post(
            spotify.SPOTIFY_TOKEN_URL,
            headers={"Authorization": f"Basic {auth_header}"},
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": script_redirect_uri,
            },
        )
        response.raise_for_status()
        token_data = response.json()

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

if __name__ == "__main__":
    main()
