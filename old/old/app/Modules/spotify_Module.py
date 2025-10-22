import spotipy
import os

# main module to mager Spotify app
class SpotifyModule:
    # begin class with parameters and authorize client
    def __init__(self,config,user):
        self.invalid = False

        client_id = config['Spotify']['client_id'][user]
        client_secret = config['Spotify']['client_secret'][user]
        redirect_url = config['Spotify']['redirect_url']

        try:
            os.environ["SPOTIPY_CLIENT_ID"] = client_id
            os.environ["SPOTIPY_CLIENT_SECRET"] = client_secret
            os.environ["SPOTIPY_REDIRECT_URI"] = redirect_url

            scope = "user-read-currently-playing, user-read-playback-state, user-modify-playback-state"
            self.auth_manager = spotipy.SpotifyOAuth(scope=scope)
            
            self.sp = spotipy.Spotify(auth_manager=self.auth_manager, requests_timeout=5)
            self.isPlaying = False
        
        except Exception as e:
            print("Error in spotify Module (get token auth): ",e)
            self.invalid = True

    # check if conection is valid
    def isInvalid(self):
        return self.invalid 
    
    # get current track on Spotify
    def getCurrentPlayback(self):
        if self.invalid:
            return None

        try:
            track = self.sp.current_user_playing_track()
            if (track is not None):
                if (track['item'] is None):
                    artist = None
                    title = None
                    art_url = None
                else:
                    artist = track['item']['artists'][0]['name']
                    if len(track['item']['artists']) >= 2:
                        artist = artist + ", " + track['item']['artists'][1]['name']
                    title = track['item']['name']
                    art_url = track['item']['album']['images'][0]['url']
                self.isPlaying = track['is_playing']
                return (artist, title, art_url, self.isPlaying, track["progress_ms"], track["item"]["duration_ms"])
            else:
                return (None, None, None, None, None, None)
        except Exception as e:
            print("Error in Spotify Module (get track)", e)
            return (None, None, None, None, None, None)
    
    # pause actual playback
    def pause_playback(self):
        if not self.invalid:
            try: self.sp.pause_playback()
            except spotipy.exceptions.SpotifyException: print('problem pausing')
            except Exception as e: print("Error in Spotify module (pause button): ", e)

    # resume actual playback
    def resume_playback(self):
        if not self.invalid:
            try:
                self.sp.start_playback()
            except spotipy.exceptions.SpotifyException:
                print('no active, trying specific device')
                devices = self.sp.devices()
                if 'devices' in devices and len(devices['devices']) > 0:
                    try:
                        self.sp.start_playback(device_id = devices['devices'][0]['id'])
                    except Exception as e:
                        print("Error in Spotify module (device id): ", e)
            except Exception as e:
                print("Error in Spotify module (play button): ",e)
    
    # pass to next track
    def next_track(self):
        if not self.invalid:
            try:
                self.sp.next_track()
            except spotipy.exceptions.SpotifyException:
                print('no active, trying specific device')
                devices = self.sp.devices()
                if 'devices' in devices and len(devices['devices']) > 0:
                    self.sp.next_track(device_id = devices['devices'][0]['id'])
            except Exception as e:
                print("Error in Spotify module (next track): ", e)

    # pass to previous track
    def previous_track(self):
        if not self.invalid:
            try:
                self.sp.previous_track()
            except spotipy.exceptions.SpotifyException:
                print('no active, trying specific device')
                devices = self.sp.devices()
                if 'devices' in devices and len(devices['devices']) > 0:
                    self.sp.previous_track(device_id = devices['devices'][0]['id'])
            except Exception as e:
                print("Error in Spotify module (previous track): ",e)

    # increase volume
    def increase_volume(self):
        if not self.invalid and self.isPlaying:
            try:
                devices = self.sp.devices()
                curr_volume = devices['devices'][0]['volume_percent']
                self.sp.volume(min(100, curr_volume + 5))
            except Exception as e:
                print("Error in Spotify module (increase volume): ",e)

    # decrease volume
    def decrease_volume(self):
        if not self.invalid and self.isPlaying:
            try:
                devices = self.sp.devices()
                curr_volume = devices['devices'][0]['volume_percent']
                self.sp.volume(max(0, curr_volume - 5))
            except Exception as e:
                print("Error in Spotify module (decrease volume): ")