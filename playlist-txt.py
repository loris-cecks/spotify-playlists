import os
from urllib.parse import urlparse
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dotenv import load_dotenv
from dataclasses import dataclass
import shutil

@dataclass
class PlaylistTrack:
    """Data class for track information"""
    title: str
    artists: str
    album: str

    def __str__(self) -> str:
        return f"{self.title} - {self.artists} - {self.album}"

class SpotifyPlaylistExporter:
    INVALID_CHARS = str.maketrans({
        '/': '-', '\\': '-', '?': '-', '%': '-', '*': '-', 
        ':': '-', '|': '-', '"': '-', '<': '-', '>': '-'
    })

    def __init__(self):
        load_dotenv()
        self._setup_environment()
        self.folder_path = self._create_export_folder()

    def _setup_environment(self) -> None:
        """Initialize Spotify client and validate environment."""
        self.spotify = self._get_spotify_client()
        self.user_id = self._validate_user_url()

    def _get_spotify_client(self) -> spotipy.Spotify:
        """Create and return authenticated Spotify client."""
        try:
            auth_manager = SpotifyOAuth(
                client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                redirect_uri="http://127.0.0.1:9090",
                scope="playlist-read-private playlist-read-collaborative",
                open_browser=True
            )
            return spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            raise RuntimeError(f"Errore di autenticazione Spotify: {e}")

    def _validate_user_url(self) -> str:
        """Extract and validate user ID from environment URL."""
        user_url = os.getenv('SPOTIFY_USER_URL')
        if not user_url:
            raise ValueError("URL utente mancante nelle variabili d'ambiente")
        
        user_id = urlparse(user_url).path.split('/')[-1]
        if not user_id:
            raise ValueError("URL utente non valido")
        return user_id

    def _create_export_folder(self) -> Path:
        """Create and return export folder path."""
        folder_path = Path(__file__).parent / 'txt'
        # Remove the folder if it exists
        if folder_path.exists():
            shutil.rmtree(folder_path)
        # Create new folder
        folder_path.mkdir(exist_ok=True)
        return folder_path

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename using translation table."""
        return filename.translate(self.INVALID_CHARS)

    def _parse_track(self, track_data: dict) -> Optional[PlaylistTrack]:
        """Parse track data into PlaylistTrack object."""
        if not track_data:
            return None
        try:
            return PlaylistTrack(
                title=track_data.get('name', 'Unknown Title'),
                artists=', '.join(artist.get('name', 'Unknown Artist') 
                                for artist in track_data.get('artists', [])),
                album=track_data.get('album', {}).get('name', 'Unknown Album')
            )
        except Exception as e:
            print(f"Errore parsing traccia: {e}")
            return None

    def _get_all_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """Fetch all tracks from a playlist with pagination."""
        tracks = []
        offset = 0
        limit = 100

        while True:
            results = self.spotify.playlist_tracks(
                playlist_id, 
                offset=offset,
                limit=limit,
                fields='items.track,next'
            )
            tracks.extend(results['items'])
            if not results.get('next'):
                break
            offset += limit

        return tracks

    def _export_playlist(self, playlist: Dict) -> None:
        """Export single playlist to file."""
        try:
            playlist_details = self.spotify.playlist(
                playlist['id'], 
                fields='name,owner.display_name,public,tracks.total'
            )
            playlist_name = self._sanitize_filename(playlist_details['name'])
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filepath = self.folder_path / f"{playlist_name}_{timestamp}.txt"

            tracks = self._get_all_playlist_tracks(playlist['id'])
            
            with filepath.open('w', encoding='utf-8') as f:
                # Write metadata
                f.write(f"Playlist: {playlist_details['name']}\n")
                f.write(f"Owner: {playlist_details['owner']['display_name']}\n")
                f.write(f"Privacy: {'Private' if not playlist.get('public', True) else 'Public'}\n")
                f.write(f"Tracks: {playlist_details['tracks']['total']}\n\n")
                f.write("=== Tracks ===\n\n")

                # Write tracks
                for item in tracks:
                    if track := self._parse_track(item.get('track')):
                        f.write(f"{track}\n")

            print(f'Playlist "{playlist_name}" salvata in:')
            print(f'  {filepath.absolute()}\n')

        except Exception as e:
            print(f"Errore esportazione playlist {playlist.get('name', 'Unknown')}: {e}")

    def export_all_playlists(self) -> None:
        """Export all user playlists."""
        try:
            playlists = []
            offset = 0
            limit = 50

            while True:
                results = self.spotify.user_playlists(self.user_id, offset=offset, limit=limit)
                playlists.extend(results['items'])
                if not results['next']:
                    break
                offset += limit

            print(f"\nInizio esportazione di {len(playlists)} playlist...")
            print(f"Cartella di destinazione: {self.folder_path.absolute()}\n")

            for playlist in playlists:
                self._export_playlist(playlist)

            print(f"\nEsportazione completata in:")
            print(f"  {self.folder_path.absolute()}")

        except Exception as e:
            raise RuntimeError(f"Errore recupero playlist: {e}")

def main() -> int:
    try:
        print("\nAvvio esportazione playlist Spotify...")
        SpotifyPlaylistExporter().export_all_playlists()
        return 0
    except Exception as e:
        print(f"\nErrore: {e}")
        return 1

if __name__ == "__main__":
    exit(main())