import os
import yaml
from datetime import datetime

class mainConfig():
    def __init__(self):
        self.config =   {'screen': {
                            'x_max': 64,
                            'y_max': 32,
                            'tam_pixel': 10,
                            'tam_space': 2},
                         'Spotify': {
                            'client_id': [''],
                            'client_secret': [''],
                            'redirect_url': 'http://localhost:8000',},
                         'Git_hub': {
                            'user':'',
                            'token':''
                         }}

    def read_config(self):
        if not os.path.exists('config'):
            os.makedirs('config')
        if os.path.isfile('config/config.yaml'):
            with open('config/config.yaml','r') as yfile:
                data = yaml.load(yfile, Loader=yaml.loader.SafeLoader)
            
            self.config = data
        else:
            print('No config file. Loading default.')
            with open('config/config.yaml','w') as yfile:
                yaml.dump(self.config,yfile) 

    def update_config(self):
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        os.rename('config/config.yaml','config/config_%s.yaml'%timestamp)
        with open('config/config.yaml','w') as yfile:
                yaml.dump(self.config,yfile)


if __name__ == "__main__":
    a = mainConfig()
    a.read_config()
