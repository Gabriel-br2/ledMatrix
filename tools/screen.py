import pygame
import numpy as np

# provisory code to simulat the screen of the aplication
# in the future will be substuited by a led matrix
class screen:
    # begin class with config
    def __init__(self,config):
        pygame.init()
        self.actual_frame = []
        self.running = True
        self.x_max = config['screen']['x_max']
        self.y_max = config['screen']['y_max']
        self.tam_pixel = config['screen']['tam_pixel']
        self.tam_space = config['screen']['tam_space']
        self.screen = pygame.display.set_mode(((self.tam_pixel*self.x_max) + (self.tam_space*(self.x_max+1)), (self.tam_pixel*self.y_max) + (self.tam_space*(self.y_max+1))))        
    
    # method to turn the mat clock wise
    # turningMat has a specific method to every app
    def turningMat(self, matriz, currentApp):
        if currentApp == 1:
            matriz1 = matriz[:, :32, :]
            matriz2 = matriz[:, 32:, :]
            return np.concatenate((np.rot90(matriz1, k=1), np.rot90(matriz2, k=1)), axis=1)
        
        elif currentApp in [2,3]:
            return matriz

    # show matrix
    def display(self,matriz,erect,currentApp):

        for event in pygame.event.get():
            if (event.type == pygame.QUIT): 
                self.running = False
        
        if not np.array_equal(matriz, self.actual_frame):            
            self.actual_frame = np.copy(matriz)

            if erect: 
                matriz = self.turningMat(matriz,currentApp)    

            self.screen.fill((37,37,37))

            y = self.tam_space 

            for j in range(32):
                x = self.tam_space
                for k in range(64):
                    try:
                        if len(matriz[j][k]) == 1: c = (matriz[j][k][0],matriz[j][k][0],matriz[j][k][0])
                        else: 
                            c = (matriz[j][k][0],matriz[j][k][1],matriz[j][k][2])
                    except:
                        c = (0,0,0)
                    pygame.draw.rect(self.screen,c,((x, y, self.tam_pixel, self.tam_pixel)))
                    x += self.tam_pixel + self.tam_space
                y += self.tam_pixel + self.tam_space

            pygame.display.flip()

            if not self.running: pygame.quit()