import numpy as np
from PIL import Image, ImageFont, ImageDraw

font = ImageFont.truetype('resource/tiny.otf', 5)

class text:
    def __init__(self, name, color, restricion=None):
        global font
        
        # make the text(name) with the color(color)
        len_name = int(font.getlength(name))

        image = Image.new('RGB', (len_name, 5), color=(0,0,0))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), name, font=font, fill=color)

        self.matText = np.array(image)
        self.matText = np.delete(self.matText, -1, axis=1)

        self.clock = 0
        self.framesMax = 0

        self.frames = self.restrict(restricion if restricion is not None else self.matText.shape[1])

    def putText(self, baseMat, cord):
        image = self.frames[self.clock]
        y,x,_ = image.shape
        baseMat[cord[1] : y + cord[1], cord[0] : x + cord[0], :] = image

        return baseMat
        
    def restrict(self, lim):
        matriz_final = []
        ini, fim = 0, lim
        image_len = self.matText.shape[0]
    
        # ajustar para efeito carrosel
        if self.matText.shape[1] > lim:
            while ini <= self.matText.shape[1]:
                sub = []
    
                for a in range(image_len):
                    subsub = self.matText[a][ini:fim,:]
                
                    if subsub.shape[0] < lim:
                        pad = np.zeros((lim - subsub.shape[0],3), dtype=self.matText.dtype)
                        subsub = np.concatenate([subsub,pad])
    
                    sub.append(subsub)
                
                matriz_final.append(sub)
                ini += 1
                fim += 1

            self.framesMax = len(matriz_final)
            return np.stack(matriz_final)
        
        else:
            pad_width = [(0, 0), (0, lim - self.matText.shape[1]), (0, 0)]
            self.matText = np.pad(self.matText, pad_width, mode='constant', constant_values=0)
            
            return [self.matText]
        
    def clockUpdate(self):
        if self.framesMax - 1 > self.clock:
            self.clock += 1
        else:
            self.clock = 0

if __name__ == "__main__":
    tittle = text("Git hub", (255,255,255), 10)
    tittle2 = text("GABRIEL ROCHA DE SOUZA", (255,0,0), 15)
    
    # main_mat = tittle.putText(main_mat, (0,0))
    # main_mat = tittle2.putText(main_mat, (10,10))

    # tittle.clockUpdate()
    # tittle2.clockUpdate()
