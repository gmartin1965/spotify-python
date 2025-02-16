import json
import spotipy
import time
import logging
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = "playlist-modify-private playlist-modify-public"

class SpotifyPlaylistManager:
    def __init__(self, config: SpotifyConfig):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            scope=config.scope
        ))
        self.user_id = self.sp.me()["id"]
        self.BATCH_SIZE = 100
        self.RATE_LIMIT_DELAY = 1

    def get_all_playlists(self) -> List[Dict[str, Any]]:
        """Fetch all playlists for the current user."""
        playlists = []
        offset = 0
        while True:
            response = self.sp.current_user_playlists(offset=offset)
            playlists.extend(response['items'])
            if len(response['items']) < 50:
                break
            offset += 50
        return playlists

    def find_playlist_by_name(self, playlist_name: str) -> Optional[str]:
        """Find a playlist by name and return its ID if found."""
        playlists = self.get_all_playlists()
        existing_playlist = next(
            (playlist for playlist in playlists if playlist['name'] == playlist_name),
            None
        )
        return existing_playlist['id'] if existing_playlist else None

    def create_playlist(self, name: str, description: str = "", public: bool = False) -> str:
        """Create a new playlist and return its ID."""
        playlist = self.sp.user_playlist_create(
            self.user_id,
            name,
            public=public,
            description=description
        )
        return playlist['id']

    def get_or_create_playlist(self, name: str, description: str = "") -> str:
        """Get existing playlist or create new one if it doesn't exist."""
        playlist_id = self.find_playlist_by_name(name)
        if playlist_id:
            print(f"Found existing playlist: {name}")
            return playlist_id

        print(f"Creating new playlist: {name}")
        return self.create_playlist(name, description)

    def should_exclude_track(self, track: Dict[str, Any], keyword: str) -> bool:
        """Check if track should be excluded based on keyword."""
        track_name = track['name'].lower()
        album_name = track['album']['name'].lower()
        artist_names = " ".join([artist['name'].lower() for artist in track['artists']])
        record_label = track['album'].get('label', '').lower()

        return any(keyword in field for field in [
            track_name,
            album_name,
            artist_names,
            record_label
        ])

    def _handle_rate_limit(self, e: spotipy.exceptions.SpotifyException, retry_count: int, max_retries: int, context: str) -> int:
        """Handle rate limit exception and return updated retry count."""
        if e.http_status == 429:
            retry_count += 1
            retry_after = int(e.headers.get('Retry-After', self.RATE_LIMIT_DELAY))
            print(f"Rate limit reached. Waiting {retry_after} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(retry_after)
        else:
            print(f"Error {context}: {e}")
            retry_count = max_retries  # Force exit from retry loop
        return retry_count

    def _process_track_with_retry(self, track_id: str, exclude_keyword: str) -> Optional[str]:
        """Process a single track with retry logic."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                track = self.sp.track(track_id)
                if not self.should_exclude_track(track, exclude_keyword):
                    return track_id
                return None

            except spotipy.exceptions.SpotifyException as e:
                retry_count = self._handle_rate_limit(e, retry_count, max_retries, f"processing track {track_id}")
            except Exception as e:
                print(f"Unexpected error processing track {track_id}: {e}")
                break
        return None

    def filter_tracks(self, track_ids: List[str], exclude_keyword: str) -> List[str]:
        """Filter track IDs based on exclusion keyword with rate limit handling."""
        filtered_tracks = []
        total_tracks = len(track_ids)
        print(f"Processing {total_tracks} tracks...")

        for i, track_id in enumerate(track_ids, 1):
            if processed_track_id := self._process_track_with_retry(track_id, exclude_keyword):
                filtered_tracks.append(processed_track_id)

            # Progress updates and rate limiting
            if i % 50 == 0:
                print(f"Processed {i}/{total_tracks} tracks...")
            if i % 10 == 0:
                time.sleep(self.RATE_LIMIT_DELAY)

        print(f"Finished processing. Found {len(filtered_tracks)} matching tracks.")
        return filtered_tracks

    def _add_batch_with_retry(self, playlist_id: str, batch: List[str], batch_number: int, total_batches: int) -> bool:
        """Add a single batch of tracks with retry logic."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                self.sp.playlist_add_items(playlist_id, batch)
                print(f"Added batch {batch_number}/{total_batches} ({len(batch)} tracks)")
                return True

            except spotipy.exceptions.SpotifyException as e:
                retry_count = self._handle_rate_limit(e, retry_count, max_retries, f"adding batch {batch_number}")
            except Exception as e:
                print(f"Unexpected error adding batch {batch_number}: {e}")
                break
        return False

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> None:
        """Add tracks to playlist in batches with rate limit handling."""
        total_batches = (len(track_ids) + self.BATCH_SIZE - 1) // self.BATCH_SIZE
        print(f"Adding tracks in {total_batches} batches...")

        for i in range(0, len(track_ids), self.BATCH_SIZE):
            batch = track_ids[i:i + self.BATCH_SIZE]
            batch_number = (i // self.BATCH_SIZE) + 1

            success = self._add_batch_with_retry(playlist_id, batch, batch_number, total_batches)

            if success and batch_number < total_batches:
                time.sleep(self.RATE_LIMIT_DELAY)



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

        # Initialize manager
        manager = SpotifyPlaylistManager(config)

        # Get track and playlist details
        track_ids = track_config['track_ids']
        playlist_name = track_config['playlist_name']
        playlist_description = track_config['playlist_description']

        # Process playlist
        playlist_id = manager.get_or_create_playlist(
            playlist_name,
            description=playlist_description
        )

        # Filter and add tracks
        filtered_tracks = manager.filter_tracks(track_ids, exclude_keyword="lofi")

        if filtered_tracks:
            manager.add_tracks_to_playlist(playlist_id, filtered_tracks)
            print(f"✅ Playlist '{playlist_name}' updated with {len(filtered_tracks)} tracks (Lofi tracks removed).")
        else:
            print("❌ No tracks added. All tracks contained 'lofi'.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
