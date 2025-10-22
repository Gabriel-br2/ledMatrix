import os
import time
import numpy as np 
from dotenv import load_dotenv

from screen import screen
from configpy import mainConfig

from app.app.gif_app import GIF 
from app.app.git_app import GIT

load_dotenv()

cfg = mainConfig()
cfg.read_config()

sideX = cfg.config['screen']['x_max']
sideY = cfg.config['screen']['y_max']

apps = [GIF(cfg.config),
        GIT(cfg.config, os.getenv('GITHUB_USER'), os.getenv('GITHUB_TOKEN'))]

app = 1
current_app = None
max_apps = len(apps)

def change_app(key):
    global app
    
    if key == "up":
        app += 1
        if app >= max_apps:
            app = 0
        
    elif key == "down":
        app -= 1
        if app < 0:
            app = max_apps -1


main_mat = np.zeros((sideY, sideX, 3))
scr = screen(cfg.config, change_app)

frame_rate = 0.05



# 0: main screen
# 1: git hub        
# 2: spotify        
# 3: gif viewer     
# 4: wather update
# 5: pet virtual
# 6: calendario       



def main(): 
    global main_mat, current_app
    
    while scr.running:
        if current_app != app:
            current_app = app
            scr.buttons(apps[current_app].buttons)
            apps[current_app].prepro()
            
        scr.display(apps[current_app].loop())
        time.sleep(frame_rate + apps[current_app].delay)

if __name__ == "__main__":
    main()