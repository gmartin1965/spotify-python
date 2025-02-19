import json
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List
from dataclasses import dataclass

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = "playlist-modify-private playlist-modify-public"

class SpotifyTrackRemover:
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

    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """Retrieve all track IDs from the given playlist."""
        existing_tracks = []
        offset = 0
        while True:
            response = self.sp.playlist_tracks(playlist_id, offset=offset)
            existing_tracks.extend([item['track']['id'] for item in response['items'] if item['track']])
            if len(response['items']) < 100:
                break
            offset += 100
        return existing_tracks

    def remove_tracks_from_playlist(self, playlist_id: str, track_ids_to_remove: List[str]) -> None:
        """Remove specified tracks from the playlist, ensuring only existing tracks are removed."""
        existing_tracks = set(self.get_playlist_tracks(playlist_id))  # Fetch current playlist tracks
        tracks_to_remove = [
            {"uri": f"spotify:track:{track_id}"} for track_id in track_ids_to_remove if track_id in existing_tracks
        ]  # Convert track IDs to URIs and ensure only valid tracks are removed

        if not tracks_to_remove:
            print("✅ No matching tracks to remove. Playlist is already clean.")
            return

        print(f"❌ Removing {len(tracks_to_remove)} tracks from playlist...")

        for i in range(0, len(tracks_to_remove), 100):  # Remove in batches of 100
            batch = [track["uri"] for track in tracks_to_remove[i:i + 100]]  # Flatten list to URIs
            try:
                self.sp.playlist_remove_all_occurrences_of_items(playlist_id, batch)
                print(f"Removed batch {i//100 + 1} of {len(tracks_to_remove)//100 + 1}")
                time.sleep(self.RATE_LIMIT_DELAY)
            except Exception as e:
                print(f"⚠️ Error removing batch: {e}")

        print(f"✅ Successfully removed {len(tracks_to_remove)} tracks.")

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
        track_config = load_config('remove_tracks.json')  # Track list file

        # Initialize Spotify config
        config = SpotifyConfig(
            client_id=spotify_config['client_id'],
            client_secret=spotify_config['client_secret'],
            redirect_uri=spotify_config['redirect_uri']
        )

        # Initialize remover
        remover = SpotifyTrackRemover(config)

        # Get playlist ID
        playlist_name = track_config['playlist_name']
        track_ids_to_remove = track_config['track_ids']
        playlist_id = remover.get_playlist_id(playlist_name)

        if not playlist_id:
            print(f"❌ Playlist '{playlist_name}' not found.")
            return

        # Remove tracks
        remover.remove_tracks_from_playlist(playlist_id, track_ids_to_remove)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
