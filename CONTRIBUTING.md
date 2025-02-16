# Contributing to Spotify Playlist Manager

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/gmartin1965/spotify-python`
3. Create a feature branch: `git checkout -b feature-name`

## Prerequisites

- Python 3.7+
- Spotify Developer Account
- Spotify API credentials

## Setting Up Development Environment

1. Create `config.json` with Spotify credentials:
```json
{
    "spotify": {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret", 
        "redirect_uri": "http://localhost:8888/callback"
    }
}
```

2. Install dependencies: `pip install -r requirements.txt`

## Making Changes

1. Write clear commit messages
2. Follow PEP 8 style guide
3. Add tests for new features
4. Update documentation

## Pull Request Process

1. Update README.md with new features/changes
2. Ensure tests pass
3. Squash commits into logical units
4. Create PR with descriptive title and detailed description

## Code of Conduct

- Be respectful and inclusive
- Welcome feedback constructively
- Maintain data privacy and security

## Development Mode Limitations

This project operates under Spotify API Development Mode, which limits access to certain endpoints including audio features. See README for details.

## Questions?

Open an issue for support questions or feature discussions.
