import os
import base64
import hashlib
from flask import Blueprint, request, redirect, session, jsonify, g
import requests
from session_store import SessionStore
from dotenv import load_dotenv

load_dotenv()

spotify_auth = Blueprint("spotify_auth", __name__)

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")
SCOPES = "user-top-read user-read-private user-read-email"

_session_store: SessionStore | None = None

def init_spotify_auth(session_store):
    global _session_store
    _session_store = session_store

def generate_pkce_pair():
    verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge

@spotify_auth.route("/spotify/login")
def login():
    # Expect the client to pass the app session id as ?session_id=...
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id required"}), 400

    verifier, challenge = generate_pkce_pair()

    # persist PKCE verifier in server-side session store for this session_id
    session_data = _session_store.get_session_data(session_id) or {}
    session_data["spotify_pkce_verifier"] = verifier
    _session_store.save_session_data(session_id, session_data)

    auth_url = (
        "https://accounts.spotify.com/authorize?"
        f"client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
        f"&code_challenge_method=S256"
        f"&code_challenge={challenge}"
        f"&state={session_id}"
    )
    return redirect(auth_url)

@spotify_auth.route("/spotify/callback")
def callback():
    code = request.args.get("code")
    state_session_id = request.args.get("state")  # our session_id passed in state
    if not code or not state_session_id:
        return "Missing code or state (session id)", 400

    # retrieve verifier saved during /spotify/login
    session_data = _session_store.get_session_data(state_session_id) or {}
    verifier = session_data.get("spotify_pkce_verifier")
    if not verifier:
        return "PKCE verifier missing for session", 400

    token_resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if token_resp.status_code != 200:
        return jsonify({"error": "Failed to exchange token", "details": token_resp.text}), 500

    data = token_resp.json()

    # Save tokens into the same session store under that session_id
    session_data["spotify_access_token"] = data.get("access_token")
    session_data["spotify_refresh_token"] = data.get("refresh_token")
    # optionally remove verifier
    session_data.pop("spotify_pkce_verifier", None)
    _session_store.save_session_data(state_session_id, session_data)

    # Redirect back to frontend so client can detect spotify_connected
    return redirect(f"{FRONTEND_URL}?spotify_connected=1")

def refresh_token(refresh_token: str):
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "client_id": CLIENT_ID,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if resp.status_code != 200:
        raise RuntimeError("Failed to refresh Spotify token")

    return resp.json()

def _get_session_tokens(session_id: str):
    if _session_store is None:
        raise RuntimeError("spotify_auth._session_store not set; set spotify_auth._session_store = session_store in app.py")
    return _session_store.get_session_data(session_id) or {}

def _ensure_valid_access_token(session_id: str):
    """
    Ensure we have a usable access token for session_id.
    - If access token exists, return it.
    - Otherwise, try to refresh using refresh_token and persist new tokens.
    """
    sd = _get_session_tokens(session_id)
    access = sd.get("spotify_access_token")
    refresh = sd.get("spotify_refresh_token")
    if access:
        return access
    if refresh:
        try:
            tokens = refresh_token(refresh)
            access = tokens.get("access_token")
            new_refresh = tokens.get("refresh_token") or refresh
            sd["spotify_access_token"] = access
            sd["spotify_refresh_token"] = new_refresh
            if _session_store is None:
                raise RuntimeError("spotify_auth._session_store not set; set spotify_auth._session_store = session_store in app.py")
            _session_store.save_session_data(session_id, sd)
            return access
        except Exception as e:
            # refresh failed
            return None
    return None

@spotify_auth.route("/spotify/user/top")
def get_user_top():
    sid = getattr(g, "session_id", None)
    if not sid:
        return jsonify({"error": "Unauthenticated"}), 401

    access = _ensure_valid_access_token(sid)
    if not access:
        return jsonify({"error": "Spotify not connected or token expired"}), 401

    headers = {"Authorization": f"Bearer {access}"}

    try:
        top_artists = requests.get(
            "https://api.spotify.com/v1/me/top/artists?limit=10",
            headers=headers,
            timeout=10
        )
        top_artists.raise_for_status()
        top_artists = top_artists.json()

        top_tracks = requests.get(
            "https://api.spotify.com/v1/me/top/tracks?limit=10",
            headers=headers,
            timeout=10
        )
        top_tracks.raise_for_status()
        top_tracks = top_tracks.json()

        profile = requests.get(
            "https://api.spotify.com/v1/me",
            headers=headers,
            timeout=10
        )
        profile.raise_for_status()
        profile = profile.json()

        return jsonify({
            "profile": profile,
            "top_artists": top_artists,
            "top_tracks": top_tracks,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@spotify_auth.route("/spotify/user/profile")
def get_spotify_user_profile():
    """Get current Spotify user info"""
    sid = getattr(g, "session_id", None)
    if not sid:
        return jsonify({"error": "Unauthenticated"}), 401

    access = _ensure_valid_access_token(sid)
    if not access:
        return jsonify({"error": "Spotify not connected or token expired"}), 401

    headers = {'Authorization': f'Bearer {access}'}

    try:
        # Get user profile
        profile_resp = requests.get("https://api.spotify.com/v1/me", headers=headers, timeout=10)
        profile_resp.raise_for_status()
        profile = profile_resp.json()

        # Get top artists
        artists_resp = requests.get("https://api.spotify.com/v1/me/top/artists?limit=10", headers=headers, timeout=10)
        artists_resp.raise_for_status()
        top_artists = artists_resp.json()

        # Get top tracks
        tracks_resp = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=10", headers=headers, timeout=10)
        tracks_resp.raise_for_status()
        top_tracks = tracks_resp.json()

        return jsonify({
            "profile": {
                "display_name": profile.get("display_name"),
                "email": profile.get("email"),
                "followers": profile.get("followers", {}).get("total"),
                "url": profile.get("external_urls", {}).get("spotify")
            },
            "top_artists": [
                {
                    "name": a.get("name"),
                    "genres": a.get("genres"),
                    "url": a.get("external_urls", {}).get("spotify")
                }
                for a in top_artists.get("items", [])
            ],
            "top_tracks": [
                {
                    "name": t.get("name"),
                    "artist": t.get("artists", [{}])[0].get("name") if t.get("artists") else "Unknown",
                    "album": t.get("album", {}).get("name"),
                    "url": t.get("external_urls", {}).get("spotify")
                }
                for t in top_tracks.get("items", [])
            ]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500