import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
import base64
import datetime

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

SCOPES = "user-read-currently-playing user-read-playback-state"


def get_auth_url():
    params = {
        "client_id": SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "scope": SCOPES,
    }
    return f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"


def get_token_data_from_code(code: str):
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
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=token_data["expires_in"]
    )
    return token_data


def refresh_access_token(refresh_token: str):
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
    token_data["expires_at"] = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=token_data["expires_in"]
    )
    return token_data


def get_user_profile(access_token: str):
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    response.raise_for_status()
    return response.json()


def get_currently_playing(access_token: str):
    response = requests.get(
        f"{SPOTIFY_API_BASE_URL}/me/player/currently-playing",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if response.status_code == 204:  # No content
        return None
    response.raise_for_status()
    return response.json()
