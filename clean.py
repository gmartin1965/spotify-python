import json
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = "playlist-modify-private playlist-modify-public"

class SpotifyPlaylistCleaner:
    def __init__(self, config: SpotifyConfig):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            scope=config.scope
        ))
        self.user_id = self.sp.me()["id"]
        self.RATE_LIMIT_DELAY = 1  # 1 second delay for rate limits

    def get_playlist_id(self, playlist_name: str) -> str:
        """Find a playlist by name and return its ID."""
        playlists = []
        offset = 0
        while True:
            response = self.sp.current_user_playlists(offset=offset)
            playlists.extend(response['items'])
            if len(response['items']) < 50:
                break
            offset += 50

        playlist = next((pl for pl in playlists if pl['name'] == playlist_name), None)
        return playlist['id'] if playlist else None

    def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, str]]:
        """Retrieve all track IDs and their associated Spotify URIs from the playlist."""
        track_list = []
        offset = 0
        while True:
            response = self.sp.playlist_tracks(playlist_id, offset=offset)
            track_list.extend([
                {"id": item['track']['id'], "uri": item['track']['uri']}
                for item in response['items'] if item['track']
            ])
            if len(response['items']) < 100:
                break
            offset += 100
        return track_list

    def remove_duplicate_tracks(self, playlist_id: str) -> None:
        """Remove duplicate tracks from a playlist, keeping only the first occurrence."""
        tracks = self.get_playlist_tracks(playlist_id)
        seen_tracks = set()
        duplicates = []

        for track in tracks:
            if track["id"] in seen_tracks:
                duplicates.append(track["uri"])
            else:
                seen_tracks.add(track["id"])

        if not duplicates:
            print("✅ No duplicate tracks found.")
            return

        print(f"❌ Found {len(duplicates)} duplicate tracks. Removing...")
        for i in range(0, len(duplicates), 100):  # Remove in batches of 100
            self.sp.playlist_remove_all_occurrences_of_items(playlist_id, duplicates[i:i + 100])
            print(f"Removed batch {i//100 + 1} of {len(duplicates)//100 + 1}")
            time.sleep(self.RATE_LIMIT_DELAY)

        print(f"✅ Successfully removed {len(duplicates)} duplicate tracks.")

def load_config(filename: str) -> dict:
    """Load configuration from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{filename} file not found")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format in {filename}")

def main():
    try:
        # Load configurations
        spotify_config = load_config('config.json')['spotify']
        track_config = load_config('track_config.json')

        # Initialize Spotify config
        config = SpotifyConfig(
            client_id=spotify_config['client_id'],
            client_secret=spotify_config['client_secret'],
            redirect_uri=spotify_config['redirect_uri']
        )

        # Initialize cleaner
        cleaner = SpotifyPlaylistCleaner(config)

        # Get playlist ID
        playlist_name = track_config['playlist_name']
        playlist_id = cleaner.get_playlist_id(playlist_name)

        if not playlist_id:
            print(f"❌ Playlist '{playlist_name}' not found.")
            return

        # Remove duplicates
        cleaner.remove_duplicate_tracks(playlist_id)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
