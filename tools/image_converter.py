import numpy as np
from PIL import Image
from io import BytesIO
import requests

class image_treatment:
  def __init__(self,img,error,types):
    self.error = error

    try:
      if types == 'image': self.img = Image.open(img)
      elif types == 'link': self.image_toPIL(img,types)
      elif types ==  'data': self.img = img
    
    except Exception as e:
         print(e)
         self.img = Image.open(self.error)
    
    self.pixels = np.asarray(self.img, np.uint8)  

  def image_toPIL(self,cont,types):
    if types == 'link': 
      ans = requests.get(cont, timeout=5)
      cont = ans.content

    elif types == 'data':
      pass
    
    image_bytes = BytesIO(cont)
    self.img = Image.open(image_bytes)

  def resize_NN_channel(self,pixels, nsize):
    nh, nw = nsize
    height, width = pixels.shape[0], pixels.shape[1]

    npixels = np.zeros(nsize, np.uint8)
    dx = (width-1)/(nw-1)
    dy = (height-1)/(nh-1)

    for i in range(nh):
      for j in range(nw):
        x, y = j*dx, i*dy
        intx, inty = int(x), int(y)
        distx, disty = x - intx, y-inty
          
        if distx > 0.5: intx = intx + 1
        if disty > 0.5: inty = inty + 1
          
        npixels[i, j] = pixels[inty, intx]
    return npixels

  def resize(self,nh,nw):
    if self.pixels.ndim == 2: 
      self.pixels = np.expand_dims(self.pixels, axis=2)
    
    self.pixels = np.transpose(self.pixels,(2,0,1))  
    channels = self.pixels.shape[0]
    self.mat_nImage = np.zeros((channels,nh,nw),np.uint8)
    
    for c in range(channels): 
      self.mat_nImage[c] = self.resize_NN_channel(self.pixels[c],(nh,nw))
    
    self.mat_nImage = np.transpose(self.mat_nImage, (1,2,0))