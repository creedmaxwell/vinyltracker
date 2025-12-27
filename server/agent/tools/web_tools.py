from smolagents import Tool, DuckDuckGoSearchTool
from bs4 import BeautifulSoup
import requests
import os
import base64
import time
from flask import g

class WebSearchTool(Tool):
    name = "web_search"
    description = (
    "Search the web for general music information. Use this tool when the user "
    "asks for recommendations, similar artists, new albums, genre exploration, "
    "music history, popularity trends, or discovering music outside the user's "
    "personal collection. "
    "This tool is NOT for retrieving the user's collection data."
    )

    inputs = {
        "question": {"type": "string", "description": "What to search for on search engine."},
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self._ddgs = DuckDuckGoSearchTool()

    def forward(self, question: str) -> str:
        query = question
        return self._ddgs(query)

class ScrapePageTool(Tool):
    name = "scrape_page"
    description = (
    "Scrape a specific webpage to extract detailed information. Use this tool "
    "after using the web search tool, when a URL has been identified that may "
    "contain relevant information (music reviews, artist details, rarity data, "
    "or record descriptions). "
    "Useful for filling in gaps when Discogs or web search results aren't "
    "sufficient."
    )
    inputs = {"url": {"type":"string","description":"HTTP/HTTPS URL to fetch"}}
    output_type = "string"

    def forward(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            return f"Request failed: {e}"
        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string.strip() if soup.title and soup.title.string else url)
        # crude extract of visible text
        for tag in soup(["script","style","noscript"]):
            tag.decompose()
        text = " ".join(t.get_text(" ", strip=True) for t in soup.find_all(["p","li","h1","h2","h3"]))
        text = " ".join(text.split())
        snippet = text[:500] + ("…" if len(text) > 500 else "")
        return f"{title}\n{snippet}"

class DiscogsSearchTool(Tool):
    name = "discogs_search"
    description = (
    "Query the Discogs API to retrieve authoritative information about a "
    "specific record (tracklist, release year, pressing details, credits, "
    "label, etc.). "
    "Use this tool when the user asks for detailed information about a specific "
    "record or when extra metadata is required about one of the user's records. "
    "When enriching a record from the user's collection, pass the `url` stored "
    "in that record's metadata as the query."
    )

    inputs = {
        "release_id": {"type": "string", "description": "Discogs release ID or URL"}
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self.token = os.getenv('DISCOGS_API_KEY')
        if not self.token:
            raise ValueError("DISCOGS_API_KEY not found in environment variables")

    def forward(self, release_id: str) -> str:
        # Clean up URL if full URL was passed
        if "discogs.com" in release_id:
            release_id = release_id.split('/')[-1]

        try:
            # Make request to Discogs API
            url = f"https://api.discogs.com/releases/{release_id}"
            headers = {
                'User-Agent': 'VinylTracker/1.0',
                'Authorization': f'Discogs token={self.token}'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Format the response
            info = [f"Title: {data.get('title', 'Unknown')}"]
            
            if data.get('artists'):
                artists = ", ".join(a.get('name', '') for a in data['artists'])
                info.append(f"Artists: {artists}")
            
            if data.get('formats'):
                formats = data['formats'][0]
                format_info = formats.get('name', '')
                if formats.get('descriptions'):
                    format_info += f" ({', '.join(formats['descriptions'])})"
                if formats.get('text'):
                    format_info += f" - {formats['text']}"
                info.append(f"Format: {format_info}")
            
            if data.get('tracklist'):
                info.append("\nTracklist:")
                for track in data['tracklist']:
                    position = track.get('position', '')
                    title = track.get('title', '')
                    duration = track.get('duration', '')
                    info.append(f"{position}. {title} {duration}")
            
            if data.get('notes'):
                info.append(f"\nNotes: {data['notes']}")

            return "\n".join(info)

        except Exception as e:
            return f"Error fetching Discogs data: {str(e)}"
        
class SpotifySearchTool(Tool):
    name = "spotify_search"
    description = (
        "Search Spotify for artist information, discography, related artists or tracks. "
        "Input should be an artist or track name. Uses public Spotify data."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "Artist name or track to search on Spotify"
        }
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise ValueError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET in environment variables.")

        self.token = None
        self.token_expiry = 0

    def _get_access_token(self):
        """Fetches a new access token using Client Credentials flow."""
        auth_str = f"{self.client_id}:{self.client_secret}"
        b64_auth = base64.b64encode(auth_str.encode()).decode()

        resp = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {b64_auth}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Spotify token error: {resp.text}")

        data = resp.json()
        self.token = data["access_token"]
        self.token_expiry = time.time() + data["expires_in"] - 60

        return self.token

    def _get_valid_token(self):
        """Returns a valid token, refreshing it if expired."""
        if not self.token or time.time() >= self.token_expiry:
            return self._get_access_token()
        return self.token

    def _get(self, url, params=None):
        token = self._get_valid_token()

        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )

        if resp.status_code == 401:
            token = self._get_access_token()
            resp = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=10,
            )

        if resp.status_code != 200:
            raise RuntimeError(f"Spotify API error {resp.status_code}: {resp.text}")

        return resp.json()

    def search_artist(self, name: str):
        url = "https://api.spotify.com/v1/search"
        params = {"q": name, "type": "artist", "limit": 5}
        data = self._get(url, params)
        return data.get("artists", {}).get("items", [])

    def search_track(self, name: str):
        url = "https://api.spotify.com/v1/search"
        params = {"q": name, "type": "track", "limit": 5}
        data = self._get(url, params)
        return data.get("tracks", {}).get("items", [])

    def get_artist_info(self, artist_id: str):
        url = f"https://api.spotify.com/v1/artists/{artist_id}"
        return self._get(url)

    def get_artist_albums(self, artist_id: str):
        url = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
        params = {"include_groups": "album,single", "limit": 10}
        return self._get(url, params).get("items", [])

    def get_related_artists(self, artist_id: str):
        url = f"https://api.spotify.com/v1/artists/{artist_id}/related-artists"
        return self._get(url).get("artists", [])

    def forward(self, query: str) -> str:
        """Search Spotify for artists or tracks."""
        query = query.strip()
        if not query:
            return "No search query provided."

        import json

        # Try searching for artist first
        artists = self.search_artist(query)
        
        # Also search for tracks
        tracks = self.search_track(query)

        result = {
            "artists": [
                {
                    "name": a.get("name"),
                    "genres": a.get("genres"),
                    "followers": a.get("followers", {}).get("total"),
                    "id": a.get("id"),
                    "url": a.get("external_urls", {}).get("spotify"),
                }
                for a in artists
            ],
            "tracks": [
                {
                    "name": t.get("name"),
                    "artist": t.get("artists", [{}])[0].get("name") if t.get("artists") else "Unknown",
                    "album": t.get("album", {}).get("name"),
                    "id": t.get("id"),
                    "url": t.get("external_urls", {}).get("spotify"),
                }
                for t in tracks
            ]
        }

        return json.dumps(result, indent=2)

class SpotifyUserTool(Tool):
    name = "spotify_user"
    description = "Get the authenticated user's Spotify profile, top artists, and top tracks"
    inputs = {}
    output_type = "string"

    def forward(self) -> str:
        """Fetch user's Spotify data from current session."""
        try:
            # Get tokens from current session (g.session_data is available in Flask context)
            session_id = getattr(g, 'session_id', None)
            session_data = getattr(g, 'session_data', {})
            
            if not session_id:
                return "Error: No session found"
            
            access_token = session_data.get('spotify_access_token')
            if not access_token:
                return "Error: Spotify not connected. User needs to connect Spotify first."
            
            headers = {'Authorization': f'Bearer {access_token}'}
            
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
            
            import json
            result = {
                "profile": {
                    "display_name": profile.get("display_name"),
                    "email": profile.get("email"),
                    "followers": profile.get("followers", {}).get("total"),
                },
                "top_artists": [
                    {
                        "name": a.get("name"),
                        "genres": a.get("genres"),
                    }
                    for a in top_artists.get("items", [])
                ],
                "top_tracks": [
                    {
                        "name": t.get("name"),
                        "artist": t.get("artists", [{}])[0].get("name") if t.get("artists") else "Unknown",
                        "album": t.get("album", {}).get("name"),
                    }
                    for t in top_tracks.get("items", [])
                ]
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return f"Error fetching Spotify user data: {str(e)}"
        