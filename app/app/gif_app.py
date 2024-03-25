from tools.image_converter import image_treatment as img_treatment
from PIL import Image
import os

class gif_View:
    # begin class with parameters
    def __init__(self,config):
        self.tamX = config['screen']['x_max']
        self.tamY = config['screen']['y_max']
        
        self.num = 0
        self.max_num = 0
        self.max_frame = 0

        self.path = []
        self.frames = []        
        self.current_gif = None

        # get path od the files in especific dir
        try:
            for actual_dir, subdirs,files in os.walk("resource/gifs/"):
                for file in files:
                    completed_path = os.path.join(actual_dir, file)
                    self.path.append(completed_path) 
            self.max_num = len(self.path)
    
        except Exception as e:
            print("Error in gif app (get path): ",e)

    # convert gif into a vector of numpy images 
    def convert_gif(self, n):
        try:
            gif = Image.open(self.path[n])
            self.frames = []
            for i in range(gif.n_frames):
                gif.seek(i)
                self.frame = gif.convert('RGB')

                img = img_treatment(self.frame, "","data")
                img.resize(32,64)
                self.frames.append(img.mat_nImage)
        
        except Exception as e:
            print("Error in gif app (conversion): ", e)        

    # main loop for this app
    def gif_loop(self, cf): 
        try:
            self.change = False
            if self.current_gif != self.num:
                self.change = True
                self.current_gif = self.num
                self.convert_gif(self.num)
            self.max_frame = len(self.frames)
            return self.frames[cf]
        
        except Exception as e:
            print("Error in gif app (main loop): ",e)

    # change the actual gif on screen
    def change_actualGIF(self):
        self.num += 1
        if self.num >= self.max_num:
            self.num = 0

    # Test the status of button and do the action of it.
    def button(self):
        try: pass 
        except Exception as e:
            print("Error in gif app (test button): ",e )