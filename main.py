import time
import numpy as np 

from tools.font import text
from tools.image_converter import image

from screen import screen
from configpy import mainConfig

cfg = mainConfig()
cfg.read_config()

sideX = cfg.config['screen']['x_max']
sideY = cfg.config['screen']['y_max']

main_mat = np.zeros((sideY, sideX, 3))
scr = screen(cfg.config)

frame_rate = 0.05

# 0: main screen
# 1: spotify        
# 2: gif viewer     
# 3: git hub        
# 4: wather update
# 5: pet virtual
# 6: calendario       

def main(): 
    global main_mat
    
    while scr.running:
        scr.display(main_mat)
        time.sleep(frame_rate)


if __name__ == "__main__":
    main()