import numpy as np
from PIL import Image
from io import BytesIO
import requests

class image:
  def __init__(self, link):
    if type(link) == str:
      if "https://" in link:
        ans = requests.get(link, timeout=5)    
        image_bytes = BytesIO(ans.content)
        img = Image.open(image_bytes)

      else:
        img = Image.open(link)

    elif type(link) == np.ndarray: 
      img = link
    
    self.img = np.asarray(img, np.uint8)  

  def resize(self, nh, nw):
    if self.img.ndim == 2: 
      self.img = np.expand_dims(self.img, axis=2)
    
    self.imgResized = np.transpose(self.img,(2,0,1))  
    channels = self.imgResized.shape[0]
    mat_nImage = np.zeros((channels,nh,nw),np.uint8)
    
    for c in range(channels): 
      mat_nImage[c] = self.resize_NN_channel(self.imgResized[c],(nh,nw))
    
    self.imgResized = np.transpose(mat_nImage, (1,2,0))

  def resize_NN_channel(self, pixels, nsize):
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

  def putImage(self, baseMat, cord):
    y, x, _ = self.imgResized.shape
    baseMat[cord[1]:y+cord[1], cord[0]:x+cord[0], :] = self.imgResized
    return baseMat

if __name__ == "__main__":
  import matplotlib.pyplot as plt
  # import tools.image_converter as Itreatment

  # test images
  path = "resource/test.jpg"
  link = "https://images.ctfassets.net/hrltx12pl8hq/7JnR6tVVwDyUM8Cbci3GtJ/bf74366cff2ba271471725d0b0ef418c/shutterstock_376532611-og.jpg"
  
  imagePath = image(path)
  imagePath.resize(32, 64)

  imageLink = image(link)
  imageLink.resize(32, 64)

  fig, axs = plt.subplots(1, 2, figsize=(10, 5))

  axs[0].imshow(imagePath.imgResized)
  axs[0].axis('off')  

  axs[1].imshow(imageLink.imgResized)
  axs[1].axis('off')  

  plt.show()