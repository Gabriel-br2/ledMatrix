import os

import spotipy

from utils import cfg
from utils.log import log


class SpotifyModule:
    def __init__(self):

        self.name: str = None
        self.image: str = None
        self.artist: str = None
        self.isPlaying: bool = False
        self.total_time: str = None
        self.actual_time: str = None

        client_id: str = os.getenv("SPOTIFY_ID")
        client_st: str = os.getenv("SPOTIFY_SECRET")
        redirect_url: str = "http://127.0.0.1:8000"

        os.environ["SPOTIPY_CLIENT_ID"] = client_id
        os.environ["SPOTIPY_CLIENT_SECRET"] = client_st
        os.environ["SPOTIPY_REDIRECT_URI"] = redirect_url

        scope: str = """user-read-currently-playing,
                        user-read-playback-state,
                        user-modify-playback-state
                     """

        self.auth_manager = spotipy.SpotifyOAuth(scope=scope, open_browser=True)
        self.spotify_API = spotipy.Spotify(
            auth_manager=self.auth_manager, requests_timeout=5
        )

    def getCurrentPlayback(self):
        try:
            track: dict = self.spotify_API.current_playback(
                additional_types=["episode"]
            )
        except:
            track = None

        if track is None:
            self.name: str = None
            self.image: str = None
            self.artist: str = None
            self.isPlaying: bool = False
            self.total_time: str = None
            self.actual_time: str = None
            return
        else:
            item = track["item"]
            if item is None:
                self.name: str = None
                self.image: str = None
                self.artist: str = None
                self.isPlaying: bool = False
                self.total_time: str = None
                self.actual_time: str = None
                return

        self.image = None
        self.name = item["name"]
        self.isPlaying = track["is_playing"]
        self.total_time = item["duration_ms"]
        self.actual_time = track["progress_ms"]

        self.artist = "Unknow"
        if track["currently_playing_type"] == "track":
            self.artist = item["artists"][0]["name"]
            if len(item["artists"]) >= 2:
                self.artist = self.artist + ", " + item["artists"][1]["name"]
            if item["album"]["images"]:
                self.image = item["album"]["images"][0]["url"]

        elif track["currently_playing_type"] == "episode":
            self.artist = item["show"]["name"]
            if item["images"]:
                self.image = item["images"][0]["url"]
            elif item["show"]["images"]:
                self.image = item["show"]["images"][0]["url"]

        log.info("Spotify data loaded")

    def pause_playback(self):
        try:
            self.spotify_API.pause_playback()
        except spotipy.exceptions.SpotifyException:
            log.warning("problem pausing")
        except Exception as e:
            log.error(f"Error in Spotify module (pause button): {e}")

    def resume_playback(self):
        try:
            self.spotify_API.start_playback()
        except spotipy.exceptions.SpotifyException:
            log.warning("no active, trying specific device")
            devices = self.spotify_API.devices()
            if "devices" in devices and len(devices["devices"]) > 0:
                try:
                    self.spotify_API.start_playback(
                        device_id=devices["devices"][0]["id"]
                    )
                except Exception as e:
                    log.error(f"Error in Spotify module (device id): {e}")
        except Exception as e:
            log.error(f"Error in Spotify module (play button): {e}")

    def next_track(self):
        try:
            self.spotify_API.next_track()
        except spotipy.exceptions.SpotifyException:
            log.warning("no active, trying specific device")
            devices = self.spotify_API.devices()
            if "devices" in devices and len(devices["devices"]) > 0:
                self.spotify_API.next_track(device_id=devices["devices"][0]["id"])
        except Exception as e:
            log.error(f"Error in Spotify module (next track): {e}")

    def previous_track(self):
        try:
            self.spotify_API.previous_track()
        except spotipy.exceptions.SpotifyException:
            log.warning("no active, trying specific device")
            devices = self.spotify_API.devices()
            if "devices" in devices and len(devices["devices"]) > 0:
                self.spotify_API.previous_track(device_id=devices["devices"][0]["id"])
        except Exception as e:
            log.error(f"Error in Spotify module (previous track): {e}")
