# Spotify Playlist Manager

A Python tool for programmatically creating and managing Spotify playlists with advanced filtering capabilities. This tool is particularly useful for handling large playlists and implementing complex filtering logic that isn't available in the Spotify UI.

## Overview

This tool allows you to:

-   Create new playlists or update existing ones
-   Filter tracks based on keywords
-   Handle large numbers of tracks with rate limiting
-   Process tracks in batches for optimal performance

## Prerequisites

1. Python 3.7 or higher
2. A Spotify account
3. Spotify Developer credentials

## Initial Setup

### 1. Spotify Developer Account

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app name and description
5. After creation, click "Settings"
6. Note down your `Client ID` and `Client Secret`
7. Add `http://localhost:8888/callback` to the Redirect URIs and save

### 2. Install Required Packages

```bash
pip install spotipy
```

### 3. Configuration Files

Create two JSON configuration files:

1. `config.json`:

```json
{
    "spotify": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "redirect_uri": "http://localhost:8888/callback"
    }
}
```

2. `track_config.json`:

```json
{
    "track_ids": ["spotify_track_id_1", "spotify_track_id_2", "..."],
    "playlist_name": "Your Playlist Name",
    "playlist_description": "Your playlist description"
}
```

## Getting Track IDs

To get track IDs efficiently:

1. Create a "Sandbox" playlist in Spotify
2. Add all potential tracks to this playlist
3. Use [Exportify](https://exportify.net/) to export your playlist to CSV
    - Exportify provides detailed track information including:
        - Track ID
        - BPM (Tempo)
        - Key
        - Acousticness
        - Instrumentalness
        - And many other audio features
4. Use Excel/Google Sheets to filter tracks based on your criteria
5. Copy the filtered track IDs to your `track_config.json`

### Exportify Tips

-   The exported CSV contains all Spotify's audio features for each track
-   You can sort and filter by any column
-   Common filtering criteria:
    -   Track length
    -   BPM (Tempo)
    -   Acousticness
    -   Instrumentalness
    -   Danceability
    -   Energy
    -   Valence (musical positiveness)

## Usage

1. Set up your configuration files as described above
2. Run the script:

```bash
python spotify.py
```

The script will:

-   Create a new playlist or use an existing one
-   Process all tracks with rate limit handling
-   Apply any filters (default filter excludes "lofi" tracks)
-   Add filtered tracks to the playlist

## Rate Limiting

The script includes built-in rate limit handling:

-   Processes tracks in batches
-   Implements automatic retries
-   Adds appropriate delays between API calls
-   Shows progress updates during processing

## Error Handling

The script provides:

-   Detailed error messages
-   Retry logic for rate limits
-   Progress updates for long operations
-   Batch processing status

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

-   [Spotipy](https://spotipy.readthedocs.io/) for the Python Spotify API wrapper
-   [Exportify](https://exportify.net/) for the playlist export functionality

## Notes

-   Keep your `config.json` secure and never commit it to version control
-   Large playlists (800+ tracks) may take some time to process due to API rate limits
-   The script can be customized to filter tracks based on different criteria
