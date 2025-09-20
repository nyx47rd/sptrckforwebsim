import os
import requests
import base64
import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# Load Spotify credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Spotify API endpoints
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

# Scopes define the permissions our app is requesting
SCOPES = "user-read-currently-playing user-read-playback-state"

def get_auth_url():
    """Constructs the Spotify authorization URL."""
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"

def get_token_data_from_code(code: str):
    """Exchanges an authorization code for an access token and refresh token."""
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")
    ).decode("ascii")

    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": SPOTIFY_REDIRECT_URI,
        },
    )
    response.raise_for_status()
    token_data = response.json()
    # Add an 'expires_at' timestamp
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=token_data["expires_in"]
    )
    return token_data

def refresh_access_token(refresh_token: str):
    """Refreshes an expired access token using a refresh token."""
    auth_header = base64.b64encode(
        f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode("ascii")
    ).decode("ascii")

    response = requests.post(
        SPOTIFY_TOKEN_URL,
        headers={"Authorization": f"Basic {auth_header}"},
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
    )
    response.raise_for_status()
    token_data = response.json()
    # Add an 'expires_at' timestamp
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=token_data["expires_in"]
    )
    return token_data

def get_user_profile(access_token: str):
    """Fetches the profile of the user associated with the access token."""
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()

def get_currently_playing(access_token: str):
    """Fetches the user's currently playing track."""
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code == 204:  # No content
        return None
    response.raise_for_status()
    return response.json()
