"""
Spotify API Connector — Current Playback and Playback Control.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import functools
import os
from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Callable
from typing import cast
from typing import TypeVar

import spotipy

from utils.log import log


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

type TrackData = dict[str, Any]

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REDIRECT_URI: str = "http://127.0.0.1:8000"
_REQUEST_TIMEOUT: int = 5

_SCOPE: str = (
    "user-read-currently-playing,"
    "user-read-playback-state,"
    "user-modify-playback-state"
)


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class PlaybackState:
    """
    Snapshot of the currently playing track or episode.
    All fields are None when nothing is playing.
    """

    name: str | None = None
    artist: str | None = None
    image: str | None = None
    is_playing: bool = False
    total_ms: int | None = None
    progress_ms: int | None = None

    def clear(self) -> None:
        """Reset to an idle / not-playing state."""
        self.name = None
        self.artist = None
        self.image = None
        self.is_playing = False
        self.total_ms = None
        self.progress_ms = None

    @property
    def has_data(self) -> bool:
        return self.name is not None


# ---------------------------------------------------------------------------
# Decorators
# ---------------------------------------------------------------------------


def _with_device_fallback(action_name: str) -> Callable[[F], F]:
    """
    Wrap a playback-control call so that if no active device is found,
    it retries automatically with the first available device ID.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(self: "SpotifyModule", *args, **kwargs) -> None:
            try:
                func(self, *args, **kwargs)
            except spotipy.exceptions.SpotifyException:
                log.warning(
                    f"[{action_name}] No active device — retrying with first available."
                )
                device_id = self._first_available_device()
                if device_id:
                    func(self, device_id=device_id, *args, **kwargs)
            except Exception as e:
                log.error(f"[{action_name}] Unexpected error: {e}")

        return cast(F, wrapper)

    return decorator


# ---------------------------------------------------------------------------
# SpotifyModule
# ---------------------------------------------------------------------------


class SpotifyModule:
    """
    Thin wrapper around the Spotipy client.

    Exposes the current playback state via :attr:`playback` and provides
    one method per control action (pause, resume, next, previous).
    Credentials are read from environment variables at construction time.
    """

    def __init__(self) -> None:
        self.playback: PlaybackState = PlaybackState()

        client_id = os.getenv("SPOTIFY_ID", "")
        client_secret = os.getenv("SPOTIFY_SECRET", "")

        if not client_id or not client_secret:
            log.warning("SPOTIFY_ID or SPOTIFY_SECRET not set in environment.")

        os.environ["SPOTIPY_CLIENT_ID"] = client_id
        os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
        os.environ["SPOTIPY_REDIRECT_URI"] = _REDIRECT_URI

        auth_manager = spotipy.SpotifyOAuth(scope=_SCOPE, open_browser=True)
        self._api: spotipy.Spotify = spotipy.Spotify(
            auth_manager=auth_manager,
            requests_timeout=_REQUEST_TIMEOUT,
        )

    # ------------------------------------------------------------------
    # Public API — data fetching
    # ------------------------------------------------------------------

    def fetch_playback(self) -> None:
        """
        Pull the current playback state from the API and update
        :attr:`playback` in-place. Clears the state on any failure.
        """
        try:
            raw: TrackData | None = self._api.current_playback(
                additional_types=["episode"]
            )
        except Exception as e:
            log.error(f"Error fetching playback: {e}")
            self.playback.clear()
            return

        if raw is None or raw.get("item") is None:
            self.playback.clear()
            return

        self._parse_playback(raw)
        log.info("Spotify playback data updated.")

    # ------------------------------------------------------------------
    # Public API — playback control
    # ------------------------------------------------------------------

    def pause(self) -> None:
        try:
            self._api.pause_playback()
        except spotipy.exceptions.SpotifyException:
            log.warning("[pause] No active device.")
        except Exception as e:
            log.error(f"[pause] Unexpected error: {e}")

    @_with_device_fallback("resume")
    def resume(self, device_id: str | None = None) -> None:
        self._api.start_playback(device_id=device_id)

    @_with_device_fallback("next_track")
    def next_track(self, device_id: str | None = None) -> None:
        self._api.next_track(device_id=device_id)

    @_with_device_fallback("previous_track")
    def previous_track(self, device_id: str | None = None) -> None:
        self._api.previous_track(device_id=device_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _first_available_device(self) -> str | None:
        """Return the ID of the first available Spotify device, or None."""
        try:
            devices = self._api.devices()
            entries = devices.get("devices", []) if devices else []
            return entries[0]["id"] if entries else None
        except Exception as e:
            log.error(f"Error fetching devices: {e}")
            return None

    def _parse_playback(self, raw: TrackData) -> None:
        """Populate :attr:`playback` from a raw API response dict."""
        item = raw["item"]
        p = self.playback

        p.is_playing = raw.get("is_playing", False)
        p.total_ms = item.get("duration_ms")
        p.progress_ms = raw.get("progress_ms")
        p.name = item.get("name")
        p.image = None

        kind: str = raw.get("currently_playing_type", "track")

        if kind == "track":
            artists = item.get("artists", [])
            p.artist = artists[0]["name"] if artists else "Unknown"
            if len(artists) >= 2:
                p.artist = (
                    p.artist + f", {artists[1]['name']}"
                    if p.artist
                    else artists[1]["name"]
                )

            images = item.get("album", {}).get("images", [])
            if images:
                p.image = images[0]["url"]

        elif kind == "episode":
            p.artist = item.get("show", {}).get("name", "Unknown")

            images = item.get("images") or item.get("show", {}).get("images", [])
            if images:
                p.image = images[0]["url"]
