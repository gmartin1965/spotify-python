import json
import spotipy
import pandas as pd
import time
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SpotifyConfig:
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str = (
        "playlist-read-private "
        "playlist-read-collaborative "
        "user-library-read "
        "user-read-private "
        "user-read-email"
    )

class SpotifyAnalyzer:
    def __init__(self, config: SpotifyConfig):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.client_id,
            client_secret=config.client_secret,
            redirect_uri=config.redirect_uri,
            scope=config.scope
        ))
        self.BATCH_SIZE = 50
        self.RATE_LIMIT_DELAY = 1

    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """Get all track IDs from a playlist."""
        tracks = []
        offset = 0

        while True:
            response = self.sp.playlist_tracks(
                playlist_id,
                offset=offset,
                fields='items.track.id,total'
            )

            if not response['items']:
                break

            tracks.extend([item['track']['id'] for item in response['items'] if item['track']])
            offset += len(response['items'])

            if offset >= response['total']:
                break

            time.sleep(self.RATE_LIMIT_DELAY)

        return tracks

    def get_audio_features(self, track_ids: List[str]) -> List[Dict]:
        """Get audio features for tracks one at a time."""
        features = []
        total_tracks = len(track_ids)

        print(f"Fetching audio features for {total_tracks} tracks...")

        for i, track_id in enumerate(track_ids, 1):
            try:
                print(f"Processing track {i}/{total_tracks}")
                feature = self.sp.audio_features(track_id)

                if feature and feature[0]:
                    features.append(feature[0])
                else:
                    print(f"No features found for track {track_id}")

                if i % 10 == 0:  # Sleep after every 10 tracks
                    time.sleep(self.RATE_LIMIT_DELAY)

            except spotipy.exceptions.SpotifyException as e:
                print(f"Error fetching features for track {track_id}: {str(e)}")
                continue

        return features

    def get_track_details(self, track_ids: List[str]) -> List[Dict]:
        """Get detailed track information in batches."""
        details = []

        for i in range(0, len(track_ids), self.BATCH_SIZE):
            batch = track_ids[i:i + self.BATCH_SIZE]
            batch_number = (i // self.BATCH_SIZE) + 1
            total_batches = (len(track_ids) + self.BATCH_SIZE - 1) // self.BATCH_SIZE

            print(f"Fetching track details: batch {batch_number}/{total_batches}")
            batch_tracks = [self.sp.track(id) for id in batch]
            details.extend(batch_tracks)

            time.sleep(self.RATE_LIMIT_DELAY)

        return details

    def analyze_playlist(self, playlist_id: str, output_file: str) -> None:
        """Analyze a playlist and export available data to CSV."""
        print("Starting playlist analysis...")

        # Get all tracks from playlist
        print("Fetching playlist tracks...")
        track_ids = self.get_playlist_tracks(playlist_id)
        total_tracks = len(track_ids)
        print(f"Found {total_tracks} tracks")

        # Get track details
        print("Fetching track details...")
        export_data = []

        for i, track_id in enumerate(track_ids, 1):
            try:
                track = self.sp.track(track_id)

                # Extract available metadata
                artists = ", ".join([artist['name'] for artist in track['artists']])

                track_data = {
                    'Track ID': track['id'],
                    'Track Name': track['name'],
                    'Artists': artists,
                    'Album': track['album']['name'],
                    'Release Date': track['album'].get('release_date', ''),
                    'Duration (ms)': track['duration_ms'],
                    'Duration (min)': round(track['duration_ms'] / 60000, 2),
                    'Popularity': track['popularity'],
                    'Preview URL': track['preview_url'],
                    'External URL': track['external_urls']['spotify'],
                    'Track Number': track['track_number'],
                    'Album Type': track['album']['album_type']
                }

                export_data.append(track_data)

                if i % 20 == 0:
                    print(f"Processed {i}/{total_tracks} tracks")
                    time.sleep(self.RATE_LIMIT_DELAY)

            except Exception as e:
                print(f"Error processing track {track_id}: {str(e)}")
                continue

        # Create DataFrame and export to CSV
        df = pd.DataFrame(export_data)
        df.to_csv(output_file, index=False)
        print(f"Analysis complete! Data exported to {output_file}")


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
        playlist_url = input("Enter Spotify playlist URL or ID: ").strip()
        playlist_id = extract_playlist_id(playlist_url)

        # Load configuration
        spotify_config = load_config('config.json')['spotify']

        # Initialize Spotify config
        config = SpotifyConfig(
            client_id=spotify_config['client_id'],
            client_secret=spotify_config['client_secret'],
            redirect_uri=spotify_config['redirect_uri']
        )

        # Initialize analyzer
        analyzer = SpotifyAnalyzer(config)

        # Set output filename
        output_file = "playlist_analysis.csv"

        # Analyze playlist and export data
        analyzer.analyze_playlist(playlist_id, output_file)

    except ValueError as e:
        print(f"Error: {e}")
        exit(1)


def extract_playlist_id(url: str) -> str:
    """
    Extract playlist ID from Spotify URL.

    Valid formats:
    - https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
    - spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
    - 37i9dQZF1DXcBWIGoYBM5M
    """
    if not url:
        raise ValueError("Please provide a Spotify playlist URL")

    # Handle spotify:playlist: URI format
    if url.startswith('spotify:playlist:'):
        return url.split(':')[-1]

    # Handle full URL format
    if 'open.spotify.com' in url:
        try:
            playlist_id = url.split('playlist/')[-1].split('?')[0]
            if not playlist_id:
                raise ValueError
            return playlist_id
        except (IndexError, ValueError):
            raise ValueError("Invalid Spotify playlist URL format")

    # Handle plain ID format
    if len(url.strip()) == 22:  # Spotify IDs are 22 characters
        return url.strip()

    raise ValueError(
        "Invalid playlist URL format. Please provide either:\n"
        "- Spotify URL (https://open.spotify.com/playlist/...)\n"
        "- Spotify URI (spotify:playlist:...)\n"
        "- Playlist ID (22 characters)"
    )

if __name__ == "__main__":
    main()