import os
from pathlib import Path
import yt_dlp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re
from dataclasses import dataclass
from typing import List
import shutil

@dataclass
class Track:
    title: str
    artists: str
    album: str

    def __str__(self) -> str:
        return f"{self.title} - {self.artists} - {self.album}"

class PlaylistDownloader:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.mp3_folder = self._create_mp3_folder()
        self.txt_folder = self.base_path / 'txt'
        self._setup_youtube_dl()

    def _create_mp3_folder(self) -> Path:
        """Create and return mp3 folder path."""
        mp3_folder = self.base_path / 'mp3'
        mp3_folder.mkdir(exist_ok=True)
        return mp3_folder

    def _setup_youtube_dl(self) -> None:
        """Configure youtube-dl options."""
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True
        }

    def _parse_txt_file(self, txt_file: Path) -> tuple[str, List[Track]]:
        """Parse a single txt file and return playlist name and list of tracks."""
        tracks = []
        playlist_name = ""
        try:
            with txt_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
                # Get playlist name from first line
                first_line = lines[0].strip()
                if first_line.startswith("Playlist: "):
                    playlist_name = first_line.replace("Playlist: ", "").strip()
                
                # Skip metadata (first 5 lines)
                for line in lines[5:]:
                    if line.strip() and ' - ' in line:
                        parts = line.strip().split(' - ')
                        if len(parts) == 3:
                            tracks.append(Track(
                                title=parts[0],
                                artists=parts[1],
                                album=parts[2]
                            ))
        except Exception as e:
            print(f"Error reading file {txt_file.name}: {e}")
        return playlist_name, tracks

    def _get_safe_filename(self, track: Track) -> str:
        """Create safe filename from track info."""
        unsafe = f"{track.title} - {track.artists}"
        # Remove or replace invalid characters
        safe = re.sub(r'[<>:"/\\|?*]', '', unsafe)
        return safe

    async def _search_and_get_url(self, track: Track) -> str:
        """Search for track on YouTube and return the best matching video URL."""
        search_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch'
        }
        
        search_query = f"{track.title} {track.artists}"
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                result = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                if result and 'entries' in result and result['entries']:
                    # Get the first search result
                    video = result['entries'][0]
                    return video.get('url') or f"https://www.youtube.com/watch?v={video['id']}"
        except Exception as e:
            print(f"Error searching for {track.title}: {e}")
        return None

    async def _download_track(self, track: Track, playlist_folder: Path) -> None:
        """Download a single track to specific playlist folder."""
        try:
            safe_filename = self._get_safe_filename(track)
            output_path = playlist_folder / f"{safe_filename}.mp3"

            # Skip if file exists
            if output_path.exists():
                print(f"Already exists: {track.title} - {track.artists}")
                return

            # Search for the video first
            video_url = await self._search_and_get_url(track)
            if not video_url:
                print(f"Could not find video for: {track.title} - {track.artists}")
                return

            # Set output template for this specific download
            download_opts = dict(self.ydl_opts)
            download_opts['outtmpl'] = str(output_path.with_suffix('.%(ext)s'))
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                try:
                    ydl.download([video_url])
                    print(f"Downloaded: {track.title} - {track.artists}")
                except Exception as e:
                    print(f"Error downloading {track.title}: {e}")

        except Exception as e:
            print(f"Error in download process for {track.title}: {e}")

    async def process_txt_folder(self) -> None:
        """Process all txt files in the txt folder."""
        if not self.txt_folder.exists():
            print("txt folder not found!")
            return

        txt_files = list(self.txt_folder.glob('*.txt'))
        if not txt_files:
            print(f"No txt files found in {self.txt_folder}")
            return

        for txt_file in txt_files:
            playlist_name, tracks = self._parse_txt_file(txt_file)
            if not playlist_name:
                print(f"Could not determine playlist name from {txt_file}")
                continue

            # Create playlist folder inside mp3 folder
            playlist_folder = self.mp3_folder / playlist_name
            playlist_folder.mkdir(exist_ok=True)

            print(f"\nFound {len(tracks)} tracks in playlist: {playlist_name}")
            print(f"MP3 files will be saved in: {playlist_folder.absolute()}\n")
            
            # Download tracks in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(
                        executor,
                        lambda t=track: asyncio.run(self._download_track(t, playlist_folder))
                    )
                    for track in tracks
                ]
                await asyncio.gather(*tasks)

    async def run(self) -> None:
        """Main execution function."""
        await self.process_txt_folder()

def main():
    try:
        downloader = PlaylistDownloader()
        asyncio.run(downloader.run())
    except KeyboardInterrupt:
        print("\nOperation interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()