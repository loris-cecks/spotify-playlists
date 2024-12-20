# Spotify Playlist to MP3 Downloader

A Python tool to export Spotify playlists and download their songs as MP3 files using YouTube as the source.

## Features

- Export all Spotify playlists to text files
- Download songs from exported playlists as MP3 files
- Parallel download processing
- Automatic playlist organization
- Sanitized filenames
- Skip existing downloads

## Requirements

- Python 3.9+
- Spotify Developer Account
- Valid Spotify API credentials

### Python Dependencies

```bash
pip install spotipy python-dotenv yt-dlp
```

### External Dependencies

- ffmpeg (required for audio conversion)

## Setup

1. Create a Spotify Developer account and create an application at <https://developer.spotify.com/dashboard>
2. Get your Client ID and Client Secret
3. Create a `.env` file in the project root with the following content:

```env
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_USER_URL=your_spotify_profile_url
SPOTIPY_REDIRECT_URI=http://127.0.0.1:9090
```

## Usage

1. First, export your Spotify playlists to text files:

```bash
python playlist-txt.py
```

This will create text files for each playlist in the `txt` folder.

2. Then, download the songs as MP3 files:

```bash
python download_songs.py
```

This will create MP3 files organized by playlist in the `mp3` folder.

## Output Structure

```
project/
├── txt/
│   ├── playlist1_timestamp.txt
│   └── playlist2_timestamp.txt
└── mp3/
    ├── playlist1/
    │   ├── song1.mp3
    │   └── song2.mp3
    └── playlist2/
        ├── song1.mp3
        └── song2.mp3
```

## Limitations

- Song matches depend on YouTube search results accuracy
- Download speed is limited to prevent API throttling
- Some songs might not be available on YouTube

## Notes

- This tool is for personal use only
- Respect copyright laws in your jurisdiction
- Some songs might not match exactly with Spotify versions

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with local laws regarding music downloading and copyright.
