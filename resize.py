import os
from PIL import Image
import torch

def resize_images():
    SOURCE = 'pokesprites/'
    DIR = 'resized/'
    
    pictures = os.listdir(SOURCE)
    print(len(pictures))
    
    try:
        os.mkdir(DIR)
    except:
        pass

    for path in pictures:
        pic = Image.open(SOURCE+path)
        if pic.size[0] != 64:
            resized = pic.resize((64, 64), Image.ANTIALIAS)
            resized.save(DIR+path, 'png')
        else:
            pic.save(DIR+path, 'png')

print(torch.version.cuda)
print(torch.cuda.is_available())
#resize_images()