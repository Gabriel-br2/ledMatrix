"""
Spotify Now-Playing Display App.
DEV     : Gabriel Rocha de Souza
PROJECT : ledMatrix
"""

import threading
from dataclasses import dataclass

import numpy as np

from app.__base__ import baseApp
from app.modules.spotify_module import SpotifyModule
from tools.font import Font
from tools.image_rescale import ImageRescale
from utils import cfg
from utils.log import log
from utils.registry import register_object


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_FONT_SIZE: int = 5
_TEXT_LIMIT: int = 30
_TEXT_OFFSET_X: int = 33
_ALBUM_SIZE: int = 32
_BUTTON_SIZE: int = 10
_PROGRESS_BAR_X: int = 34
_PROGRESS_BAR_Y: int = 18
_PROGRESS_BAR_MAX: int = 27
_BUTTON_POS_Y: int = 21
_BUTTON_POS_X: int = 43

_COLOR_BAR_BG: tuple = (44, 86, 60)
_COLOR_BAR_FG: tuple = (50, 236, 108)
_COLOR_ICON_MASK: tuple = (255, 255, 255)

_PLAYBACK_UPDATE_FRAME: int = 1  # fetch new data on this frame index

# Truncation heuristic: if one string is 3× longer than the other, truncate it.
_TRUNCATION_RATIO: float = 3.0


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class _TextState:
    """Groups the two scrolling Font objects for title and artist."""

    title: Font
    artist: Font

    def sync_frames(self) -> int:
        """Align both fonts to the same total frame count. Returns that count."""
        total = max(self.title.frames, self.artist.frames)
        self.title.extern_limit(total)
        self.artist.extern_limit(total)
        return total

    def reset_position(self) -> None:
        self.title.actual_frame = 0
        self.artist.actual_frame = 0

    def advance(self) -> None:
        self.title += 1
        self.artist += 1

    def put(self, base: np.ndarray) -> np.ndarray:
        base = self.title.put(base=base)
        base = self.artist.put(base=base)
        return base

    def update_texts(self, title: str, artist: str) -> None:
        self.title.update_text(title)
        self.artist.update_text(artist)
        self.reset_position()
        self._apply_limits()

    def _apply_limits(self) -> None:
        self.title.limit(_TEXT_LIMIT)
        self.artist.limit(_TEXT_LIMIT)
        total = self.sync_frames()
        self.title.carousel()
        self.artist.carousel()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@register_object("app", "spotify")
class SpotifyApp(baseApp):
    """
    Displays the currently playing Spotify track with album art, a progress
    bar, and a play/pause button icon.

    The playback state is refreshed on a background thread every
    ``_PLAYBACK_UPDATE_FRAME`` ticks to avoid blocking the render loop.
    """

    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="Spotify")

        self.path: str = cfg.config["main"]["path"]
        self.fps_app: float = 0.1
        self.total_frames: int | None = 20

        self._module: SpotifyModule = SpotifyModule()

        self._album_art: ImageRescale = self._load_disconnected_art()
        self._btn_icon: ImageRescale = self._load_button_icon(playing=False)
        self._is_playing: bool = False
        self._last_track: str | None = None

        self._text: _TextState = _TextState(
            title=Font(size=_FONT_SIZE, text="Title: None", offset=(2, _TEXT_OFFSET_X)),
            artist=Font(
                size=_FONT_SIZE, text="Artist: None", offset=(10, _TEXT_OFFSET_X)
            ),
        )
        self._text._apply_limits()

    # ------------------------------------------------------------------
    # baseApp contract
    # ------------------------------------------------------------------

    def main_loop_app(self, base: np.ndarray) -> np.ndarray:
        if self.actual_frame == _PLAYBACK_UPDATE_FRAME:
            threading.Thread(target=self._fetch_and_update, daemon=True).start()

        # Album art (32×32 top-left)
        base[0:_ALBUM_SIZE, 0:_ALBUM_SIZE] = self._album_art.resized

        # Progress bar background
        base[
            _PROGRESS_BAR_Y, _PROGRESS_BAR_X : _PROGRESS_BAR_X + _PROGRESS_BAR_MAX + 1
        ] = _COLOR_BAR_BG

        # Progress bar fill
        p = self._module.playback
        if p.total_ms:
            filled = self._progress_pixels(p.total_ms, p.progress_ms or 0)
            base[_PROGRESS_BAR_Y, _PROGRESS_BAR_X : _PROGRESS_BAR_X + filled] = (
                _COLOR_BAR_FG
            )

        # Play/pause button icon — mask white pixels to bar-bg color
        icon = (
            self._btn_icon.resized.copy()
            if self._btn_icon.resized is not None
            else np.zeros((_BUTTON_SIZE, _BUTTON_SIZE, 3), dtype=np.uint8)
        )
        mask = np.all(icon == list(_COLOR_ICON_MASK), axis=2)
        icon[mask] = _COLOR_BAR_BG
        base[
            _BUTTON_POS_Y : _BUTTON_POS_Y + _BUTTON_SIZE,
            _BUTTON_POS_X : _BUTTON_POS_X + _BUTTON_SIZE,
        ] = icon

        # Scrolling text
        base = self._text.put(base)
        self._text.advance()

        return base

    def on_exit(self) -> None:
        pass

    def _button_short_click(self) -> None:
        # Uncomment to enable pause/resume on short click:
        # if self._module.playback.is_playing:
        #     self._module.pause()
        # else:
        #     self._module.resume()
        pass

    def _button_left(self) -> None:
        # self._module.previous_track()
        pass

    def _button_right(self) -> None:
        # self._module.next_track()
        pass

    def _button_long_click(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _fetch_and_update(self) -> None:
        """Fetch playback data and update visuals if the track changed."""
        self._module.fetch_playback()
        p = self._module.playback

        # Update album art and text only when the track changes.
        if p.name != self._last_track and p.name is not None:
            self._last_track = p.name

            self._album_art = ImageRescale(
                source=p.image or "",
                scale=(_ALBUM_SIZE, _ALBUM_SIZE),
                fallback=self.path + "resource/Spotify_NConnected.jpg",
            )

            title_display, artist_display = self._truncate_texts(
                p.name, p.artist or "Unknown"
            )
            self._text.update_texts(
                title=f"Title: {title_display}",
                artist=f"Artist: {artist_display}",
            )

        # Update play/pause button icon if state changed.
        if p.is_playing != self._is_playing:
            self._is_playing = p.is_playing
            self._btn_icon = self._load_button_icon(playing=self._is_playing)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _progress_pixels(self, total_ms: int, progress_ms: int) -> int:
        return (_PROGRESS_BAR_MAX * progress_ms) // total_ms + 1

    def _load_disconnected_art(self) -> ImageRescale:
        return ImageRescale(
            source=self.path + "resource/Spotify_NConnected.jpg",
            scale=(_ALBUM_SIZE, _ALBUM_SIZE),
        )

    def _load_button_icon(self, playing: bool) -> ImageRescale:
        label = "pause" if playing else "play"
        return ImageRescale(
            source=self.path + f"resource/button/{label}_sp.png",
            scale=(_BUTTON_SIZE, _BUTTON_SIZE),
        )

    @staticmethod
    def _truncate_texts(name: str, artist: str) -> tuple[str, str]:
        """
        If one string is more than *_TRUNCATION_RATIO*× longer than the other,
        truncate it to keep both labels visually balanced.
        """
        min_len = min(len(name), len(artist))
        max_len = max(len(name), len(artist))

        if min_len == 0 or max_len <= _TRUNCATION_RATIO * min_len:
            return name, artist

        break_at = int(min_len * 2.25)

        if len(name) == max_len:
            return f"{name[:break_at]}…", artist
        return name, f"{artist[:break_at]}…"
