from app.Modules.spotify_Module import SpotifyModule as Spotify
from tools.image_converter import image_treatment as img_treatment
from tools.font import FONT

class Spoty:
    # begin class spoty with parameters 
    def __init__(self,cfg):
        self.cfg = cfg

        self.track = [0,0,0]
        self.color = [0,0,0]

        self.F = FONT()
        self.spotify = Spotify(cfg,0)

        self.bar = None
        self.img_track = None
        self.text_title = []
        self.text_artist = []
        self.current_track = 0

    # Create matrix of colors
    def create_mat(self):
        try:
            self.current_track = self.track[1]
            
            # generate text and put limit
            if self.track[0] == None: title, artist =  'not Conected', ' '
            else: artist, title = self.track[0:2]

            self.text_title = self.F.pixel(title,(255,255,255))
            self.text_title = self.F.limited(self.text_title,30)

            self.text_artist = self.F.pixel(artist,(175,175,175))
            self.text_artist = self.F.limited(self.text_artist,30)

            # genereate image
            img = img_treatment(self.track[2], "resource/Spotify_NConnected.jpg","link")
            img.resize(32,32)
            self.img_track = img.mat_nImage
        
        except Exception as e:
            print("Error in Spotify app (create mat): ",e)

    # generate progress bar
    def progress_bar(self,actual,total):
        try:
            result = []
            
            if total != None: normalized_value = actual/total
            else: normalized_value = 1
            new_value = 28 * normalized_value

            for a in range(28):
                if a <= new_value: result.append(self.color)
                else: result.append((0,0,0))
            return result
        
        except Exception as e:
            print("Error in Spotify app (progress bar): ",e)
            return [(0,0,0)]*28

    # Get de main reference color of the image
    def get_color(self):
        try:
            c,mr,mg,mb = 0,0,0,0
            for a in range(32):
                for b in range(32):
                    mr += self.img_track[a][b][0] 
                    mg += self.img_track[a][b][1]
                    mb += self.img_track[a][b][2]
                    c += 1
            self.color = (mr//c,mg//c,mb//c)
       
        except Exception as e:
            print("Error in Spotify app (get color): ",e)
            self.color = (0,0,0) 

    # Put the data in the main matrix
    def puting_data(self, main_mat,cf):
        try:
            self.bar = self.progress_bar(self.track[4],self.track[5])
        
            try: main_mat[5:10,33:33+30,:] = self.text_title[cf]
            except IndexError: pass
            
            try: main_mat[13:18,33:33+30,:] = self.text_artist[cf]
            except IndexError: pass
        
            main_mat[24:25,34:62,:] = self.bar
        
        except TypeError: pass
        except Exception as e: print("Error in Spotify app (puting data): ", e)
        return main_mat

    # main loop of spoty app
    def spoty_loop(self,main_mat,cf,delay):
        try:
            self.change = False
            
            # get current track self.change = Falseon spotify
            self.track = self.spotify.getCurrentPlayback()

            # main setup only if new data
            if self.track[1] != self.current_track:
                self.change = True
                self.create_mat()
                self.get_color()

                # puting img in to main matrix
                main_mat[:,:32,:] = self.img_track
                
            # do the delay
            if cf <= delay: cf = 0
            else: cf -= delay

            # draw data
            self.puting_data(main_mat,cf)

            return main_mat

        except Exception as e:
            print("Error in Spotify app (main loop): ", e)
            return main_mat

    def actions(self,action):
        if action == 'play':           self.spotify.resume_playback()
        elif action == 'pause':        self.spotify.pause_playback()
        elif action == 'next':         self.spotify.next_track()
        elif action == 'prev':         self.spotify.previous_track()
        elif action == 'increase_vol': self.spotify.increase_volume()
        elif action == 'decrease_vol': self.spotify.decrease_volume()

    # Test the status of button and do the action of it.
    def button(self):
        try: pass
        except Exception as e:
            print("Error in Spotify app (test button): ",e ) 