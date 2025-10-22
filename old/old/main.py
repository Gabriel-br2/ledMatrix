import time
import numpy as np
from tools.screen import screen
from old.configpy import mainConfig
from app.app.spotify_app import Spoty
from app.app.gif_app import gif_View
from app.app.Github_app import git

cfg = mainConfig()
cfg.read_config()

main_mat = np.zeros(
    (cfg.config['screen']['y_max'], 
     cfg.config['screen']['x_max'], 3))

scr = screen(cfg.config)
sptf = Spoty(cfg.config)
gifv = gif_View(cfg.config)
github = git(cfg.config)

current_frame = 0
current_app = 1
delay = 10

gifv.num=1

# 0: main screen
# 1: spotify        OK
# 2: gif viewer     OK
# 3: git hub        OK
# 4: wather update
# 5: pet virtual
# 6: calendario       

def main(): 
    global current_frame
    global current_app
    global delay

    while scr.running:
        if current_app == 1:
            main_mat = sptf.spoty_loop(main_mat, current_frame, delay)
            max_frames = max((len(sptf.text_title), len(sptf.text_artist))) + delay
            if current_frame >= max_frames or sptf.change:
                current_frame = 0

        if current_app == 2:
            main_mat = gifv.gif_loop(current_frame)
            max_frames = gifv.max_frame-1
            if current_frame >= max_frames or gifv.change:
                current_frame = 0
            time.sleep(0.1)

        if current_app == 3:
            main_mat = github.git_loop()
            max_frames = 0
            if current_frame >= max_frames or False:
                current_frame = 0

        #if current_app == 4:

        erect = False
        scr.display(main_mat, erect, current_app)
        current_frame += 1

main()