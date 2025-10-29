import os
import threading

import numpy as np

from app.__base__ import baseApp
from app.modules.spotify_module import SpotifyModule
from tools.font import Font
from tools.image_rescale import image
from utils import cfg
from utils.log import log
from utils.registry import register_object


@register_object("app", "spotify")
class app(baseApp):
    def __init__(self, app_id: int = 0) -> None:
        super().__init__(app_id=app_id, name="spotify")
        self.path: str = cfg.config["main"]["path"]

        self.fps_app: float = 0.1
        self.bar_max: int = 27
        self.total_frames: int = 20
        self.playback_actual_name: str = None

        self.spotipy: SpotifyModule = SpotifyModule()

        self.image_track = image(
            img=self.path + "resource/Spotify_NConnected.jpg", scale=(32, 32)
        )

        self.actual_button: bool = False
        self.image_button = image(
            img=self.path + "resource/button/play_sp.png", scale=(10, 10)
        )

        self.tittle_track = Font(tam=5, text="Tittle: None", offset=(2, 33))

        self.Artist_track = Font(tam=5, text="Artist: None", offset=(10, 33))

        self.calibrate_texts()

    def get_proporsion(self, total_music: int, now_music: int) -> int:
        return (self.bar_max * now_music) // total_music

    def calibrate_texts(self):
        self.tittle_track.limit(lim=30)
        self.Artist_track.limit(lim=30)

        extern: int = max(self.tittle_track.frames, self.Artist_track.frames)

        self.tittle_track.extern_limit(lim=extern)
        self.Artist_track.extern_limit(lim=extern)

        self.tittle_track.carousel()
        self.Artist_track.carousel()

    def threading_info(self):
        self.spotipy.getCurrentPlayback()

        if (
            self.playback_actual_name != self.spotipy.name
            and self.spotipy.name is not None
        ):
            self.playback_actual_name = self.spotipy.name

            if self.spotipy.image:
                self.image_track = image(
                    img=self.spotipy.image,
                    scale=(32, 32),
                    error=self.path + "resource/Spotify_NConnected.jpg",
                )

            if self.spotipy.name and self.spotipy.artist:
                min_len = min(len(self.spotipy.name), len(self.spotipy.artist))
                max_len = max(len(self.spotipy.name), len(self.spotipy.artist))

                name_display = self.spotipy.name
                artist_display = self.spotipy.artist

                if max_len > 3 * min_len:
                    break_at = int(min_len * 2.25)

                    if len(self.spotipy.name) == max_len:
                        name_display = f"{self.spotipy.name[:break_at]}..."
                    else:
                        artist_display = f"{self.spotipy.artist[:break_at]}..."

                self.tittle_track.update_text(text=f"Tittle: {name_display}")
                self.Artist_track.update_text(text=f"Artist: {artist_display}")

                self.tittle_track.actual_frame = 0
                self.Artist_track.actual_frame = 0

                self.calibrate_texts()

        if self.actual_button != self.spotipy.isPlaying:
            d = {False: "play", True: "pause"}

            self.actual_button = self.spotipy.isPlaying
            self.image_button = image(
                img=self.path + f"resource/button/{d[self.actual_button]}_sp.png",
                scale=(10, 10),
            )

    def main_loop_app(self, base: np.array) -> None:
        if self.actual_frame == 1:
            thread_load = threading.Thread(target=self.threading_info)
            thread_load.start()

        base = self.tittle_track.put(base=base)
        base = self.Artist_track.put(base=base)

        base[0:32, 0:32] = self.image_track.resized
        base[18, 34 : 35 + self.bar_max] = (44, 86, 60)

        if self.spotipy.total_time:
            temp = (
                self.get_proporsion(
                    total_music=self.spotipy.total_time,
                    now_music=self.spotipy.actual_time,
                )
                + 1
            )

            base[18, 34 : 34 + temp] = (50, 236, 108)

        mask = np.all(self.image_button.resized == [255, 255, 255], axis=2)
        self.image_button.resized[mask] = (44, 86, 60)

        base[21 : 21 + 10, 43 : 43 + 10] = self.image_button.resized

        self.tittle_track += 1
        self.Artist_track += 1

        return base

    def on_exit(self) -> None:
        pass

    def _button_left(self) -> None:
        return
        self.spotipy.previous_track()

    def _button_right(self) -> None:
        return
        self.spotipy.next_track()

    def _button_short_click(self) -> None:
        return
        if self.spotipy.isPlaying:
            self.spotipy.pause_playback()
        else:
            self.spotipy.resume_playback()

    def _button_long_click(self) -> None:
        pass
