import numpy as np
from PIL import Image, ImageFont, ImageDraw

class FONT:
    def __init__(self):
        self.font = ImageFont.truetype('config/tiny.otf',5)
    
    # make the text(name) with the color(color)
    def pixel(self,name,color):

        len_name = int(self.font.getlength(name)) #self.font.textsize(name, font=self.font)[0] 

        image = Image.new('RGB', (len_name, 5), color=(0,0,0))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), name, font=self.font, fill=color)

        image_mat = np.array(image)
        image_mat = np.delete(image_mat, -1, axis=1)
        return image_mat

    # put a limit in the X axis and put one more dimension
    def limited(self,image_mat,lim):
        matriz_final = []
        ini,fim = 0,lim
        image_len = image_mat.shape[0]

        if image_mat.shape[1] > lim:
            while ini <= image_mat.shape[1]:
                sub = []

                for a in range(image_len):
                    subsub = image_mat[a][ini:fim,:]
                
                    if subsub.shape[0] < lim:
                        pad = np.zeros((lim - subsub.shape[0],3), dtype=image_mat.dtype)
                        subsub = np.concatenate([subsub,pad])

                    sub.append(subsub)
                
                matriz_final.append(sub)
                ini += 1
                fim += 1

            return np.stack(matriz_final)
        
        else:
            pad_width = [(0, 0), (0, 30 - image_mat.shape[1]), (0, 0)]
            image_mat = np.pad(image_mat, pad_width, mode='constant', constant_values=0)
            
            return [image_mat]