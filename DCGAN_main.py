# -*- coding: utf-8 -*-
"""V2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WymuyV6287q5n-LFy4g-bcNwc9eLXrd8
"""

import os
import urllib.request
from random import randint
import random
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
import copy
import numpy as np
import matplotlib.pyplot as plt

#For using the dataset when it's stored on Drive.

#from google.colab import drive
#drive.mount("/content/gdrive")

# Miscellaneous parameters

batch_size = 128 # First tried 64 as in Pytorch doc
n_epochs = 125
image_size = 64
workers = 1 # for dataloader

# Decide which device (gpus or cpu) we want to run on
ngpu = 1 # number of gpus, 1 on Colab
device = torch.device("cuda:0" if (torch.cuda.is_available() and ngpu > 0) else "cpu")


"""
With batch size of 128 (recommended in paper) it took 8 epochs for generator 
to output something over than pure white (actually purple) noise. 
Nvm it seems my code is wrong. 
I take back everything, it outputted something neat.
Well, not that neat, but it's something that with batch_size = 64 would have 
come at epoch 10 or something.
"""

# Loading and visualizing the data


# Root directory for dataset, change accordingly
dataroot = "/content/gdrive/My Drive/data/"


# Create the dataset
dataset = dset.ImageFolder(root=dataroot,
                           transform=transforms.Compose([
                               transforms.CenterCrop(image_size),
                               transforms.ToTensor(),
                               transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                           ]))

# Create the dataloader
dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                         shuffle=True, num_workers=workers,
                                         drop_last=True)

# Plot some training images
real_batch = next(iter(dataloader))
plt.figure(figsize=(8,8))
plt.axis("off")
plt.title("Training Images")
plt.imshow(np.transpose(vutils.make_grid(real_batch[0].to(device)[:64], padding=2, normalize=True).cpu(),(1,2,0)))
plt.show()

# Set random seed for reproducibility
manualSeed = 777
#manualSeed = random.randint(1, 10000) # use if you want new results
print("Random Seed: ", manualSeed)
random.seed(manualSeed)
torch.manual_seed(manualSeed)
print(device)

# Creating Generator and Discriminator (=Critic)

import torch
import torch.nn as nn

noise_dim = 100 # dimension of noise vector
num_ch = 3 # number of channels
n_gen_f = 64 # generator feature map size
n_disc_f = 64 # discriminator feature map size


#### Generator

class Generator(nn.Module):
    def __init__(self):
      super(Generator, self).__init__()
      self.main = nn.Sequential(
          # as in paper's code (4x4 kernel instead of 5x5), 64*16 = 1024 channel output
          nn.ConvTranspose2d(noise_dim, n_gen_f*8*2, 4, 1, 0, bias=False), # 4x4 imgs, ch = 1024
          nn.BatchNorm2d(n_gen_f*8*2),
          nn.ReLU(),

          nn.ConvTranspose2d(n_gen_f*8*2, n_gen_f*4*2, 4, 2, 1, bias=False), # 8x8 imgs, ch = 512
          nn.BatchNorm2d(n_gen_f*4*2), # *8
          nn.ReLU(),

          nn.ConvTranspose2d(n_gen_f*4*2, n_gen_f*2*2, 4, 2, 1, bias=False), # 16x16 imgs, ch = 216
          nn.BatchNorm2d(n_gen_f*2*2), # *4
          nn.ReLU(),

          nn.ConvTranspose2d(n_gen_f*2*2, n_gen_f*2, 4, 2, 1, bias=False), # 32x32 imgs, ch = 128
          nn.BatchNorm2d(n_gen_f*2), # *2
          nn.ReLU(),

          nn.ConvTranspose2d(n_gen_f*2, num_ch, 4, 2, 1, bias=False), # 64x64 imgs, ch = 3
          nn.Tanh(),
          # returns 64x64x3 image
      )

    def forward(self, input):
      return self.main(input)


#### Discriminator (Critic)

class Discriminator(nn.Module):
    def __init__(self):
      super(Discriminator, self).__init__()
      self.main = nn.Sequential(
          # Inverse structure to Generator 
          # 64x64x3 img input
          nn.Conv2d(num_ch, n_disc_f*2, 4, 2, 1, bias=False),  
          nn.LeakyReLU(0.2),

          nn.Conv2d(n_disc_f*2, n_disc_f*2*2, 4, 2, 1, bias=False), 
          nn.BatchNorm2d(n_disc_f*2*2),
          nn.LeakyReLU(0.2),

          nn.Conv2d(n_disc_f*2*2, n_disc_f*4*2, 4, 2, 1, bias=False),
          nn.BatchNorm2d(n_disc_f*4*2),
          nn.LeakyReLU(0.2),

          nn.Conv2d(n_disc_f*4*2, n_disc_f*8*2, 4, 2, 1, bias=False),
          nn.BatchNorm2d(n_disc_f*8*2),
          nn.LeakyReLU(0.2),

          nn.Conv2d(n_disc_f*8*2, 1, 4, 1, 0, bias=False),
          nn.Sigmoid()
          # Returns scalar: evaluation of how real the input image is
        )
    
    def forward(self, input):
      return self.main(input)

"""
Note: initially, the generator's parameters had been set to be exactly that of 
the paper's. That is, the number of output channels was double of what it 
currently is (comments have been left as they were to showcase that). 
Now setting discriminator to mirror the generator's architecture as output with 
this generator wasn't bad.
"""

# Weight initialization function:

def initialize_weights(model):
    # Initializes weights according to the DCGAN paper
    for m in model.modules():
        if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d, nn.BatchNorm2d)):
            nn.init.normal_(m.weight.data, 0.0, 0.02)
"""
Difference with Pytorch doc: batchNorm has different norm vals, mean = 1.0,
Where that comes from I don't know.
"""

# Model initialization

netG = Generator().to(device) 
netD = Discriminator().to(device)

# Initializing weight following above normal distribution
netG.apply(initialize_weights)
netD.apply(initialize_weights)

# Setting up for training 

from torch.nn.modules.loss import BCELoss
import torch.optim as optim

# Hyperparams

lr = 0.0002 # Learning rate
lr_g = lr # lr of generator
lr_d = lr # lr of discriminator
beta1 = 0.5 # recommended Adam optimizer parameter
# beta2 is left to default .999
label_real = 0.9 # smoothed label for real images
label_fake = 0

# Create batch of latent vectors that we will use to visualize
# the progression of the generator
fixed_noise = torch.randn(64, noise_dim, 1, 1, device=device)

optG = optim.Adam(netG.parameters(),lr=lr_g,betas=(beta1,0.999))
optD = optim.Adam(netD.parameters(),lr=lr_g,betas=(beta1,0.999))

loss_func = BCELoss() # using BCE to compute loss

black = torch.tensor(-1.)#.to(device) # Do not send to device.
# All tensors are normalized between -1 and 1, with -1 corresponding to black

def change_bg_to_black(imgs):
  """
  Given a set of 128 imgs of dim 3*64*64, sets the background colour to black.
  This function is imperfect, as it merely changes all colours == bg_colour 
  to black, but it should work well enough (not too many issues).
  """
  for img in imgs:

    # each channel may have a different bg colour, we check them individually
    for channel in range(len(img)):
        bg_colour = img[channel,0,0] # 1st pixel always has same colour as bg
        if bg_colour != black:
          img[channel] = torch.where(img[channel] == black, img[channel], black)

  return imgs

# Commented out IPython magic to ensure Python compatibility.
# Main training loop

# To keep track of progress
img_list = []
img_list_rand = []
G_losses = []
D_losses = []
iters = 0

print("Consider making a cup of coffee in the meantime")
for epoch in range(n_epochs):
  for batch_i, real_imgs in enumerate(dataloader, 0):
    #print('Iteration n??%d' % (batch_i+1))
    # zeroing gradients at each loop
    netD.zero_grad()
    netG.zero_grad()

    # This loop's images:
    real_imgs = real_imgs[0].to(device) # retrieving real imgs
    #real_imgs = change_bg_to_black(real_imgs[0]).to(device)

    noise = torch.randn(batch_size, noise_dim, 1, 1, device=device)
    fake_imgs = netG(noise) # generating fake ones

    # Creating label tensors to compute loss
    label_r = torch.full((batch_size,), label_real, dtype=torch.float, device=device) 
    # full of 0.9's
    label_f = torch.full((batch_size,), label_fake, dtype=torch.float, device=device) 
    # full of 0's


    ############################
    # (1) Update D network: maximize log(D(x)) + log(1 - D(G(z)))
    ############################

    #### (1.1) Training on real images
    # Forward pass
    # score on batch of real imgs
    outputR = netD(real_imgs).view(-1) # flattens the matrix 
    lossD_real = loss_func(outputR,label_r)
    # Backward pass to get gradients
    lossD_real.backward()

    #### (1.2) Training on fake images
    # Forward pass
    outputF = netD(fake_imgs.detach()).view(-1)
    lossD_fake = loss_func(outputF,label_f)
    # Backward pass to get gradients
    lossD_fake.backward()

    # Optimization step
    optD.step()


    ############################
    # (2) Update G network: maximize D(G(z))
    ############################

    # We've already generated the fake images and scored them 
    # But D has been updated -> get them scored again to obtain D(G(z))
    output = netD(fake_imgs).view(-1)
    # no use generating new fake imgs, G hasn't been updated yet
    lossG = loss_func(output,label_r) # To G, its images count as real ones
    # so we use label_real
    lossG.backward()

    # Optimization step
    optG.step()


    ###########################
    # This section is to keep track of progress, irrelevant to actual workings
    ###########################
    lossD = lossD_fake + lossD_real 
    D_x = outputR.mean() # D(x)
    D_G_z1 = outputF.mean() # D(G(z)) before update of Discriminator
    D_G_z2 = output.mean() # D(G(z)) after update of Discriminator

    if batch_i % 5 == 0:
        print('[%d/%d][%d/%d]\tLoss_D: %.4f\tLoss_G: %.4f\tD(x): %.4f\tD(G(z)): %.4f / %.4f'
#               % (epoch+1, n_epochs, batch_i, len(dataloader),
                  lossD.item(), lossG.item(), D_x, D_G_z1, D_G_z2))

    # Save Losses for plotting later
    G_losses.append(lossG.item())
    D_losses.append(lossD.item())

    # Check how the generator is doing by saving G's output on fixed_noise
    if (iters % len(dataloader) == 0) or ((epoch == n_epochs-1) and (batch_i == len(dataloader)-1)):
        rand_noise = torch.randn(64, noise_dim, 1, 1, device=device)
        with torch.no_grad():
            fake = netG(fixed_noise).detach().cpu()
            fake_rand = netG(rand_noise).detach().cpu()
        img_list.append(vutils.make_grid(fake, padding=2, normalize=True))
        img_list_rand.append(vutils.make_grid(fake_rand, padding=2, normalize=True))

    iters += 1

  # Plot the fake images from fixed noise after every epoch to see how output 
  # changes
  plt.subplot(1,2,1)
  plt.axis("off")
  plt.title("Fake Images (fixed noise)")
  plt.imshow(np.transpose(img_list[-1],(1,2,0)))

  # Plot fake images from randomised noise at each epoch 
  plt.subplot(1,2,2)
  plt.axis("off")
  plt.title("Fake Images (random noise)")
  plt.imshow(np.transpose(img_list_rand[-1],(1,2,0)))

  plt.show()

plt.figure(figsize=(10,5))
plt.title("Generator and Discriminator Loss During Training")
plt.plot(G_losses,label="G")
plt.plot(D_losses,label="D")
plt.xlabel("iterations")
plt.ylabel("Loss")
plt.legend()
plt.show()

# Transofrms saved images of the fixed noise into GIF so we may see
# the evolution of the generator's output
import matplotlib.animation as animation
from IPython.display import HTML

fig = plt.figure(figsize=(8,8))
plt.axis("off")
ims = [[plt.imshow(np.transpose(i,(1,2,0)), animated=True)] for i in img_list[len(img_list)//2:]] # choose index at will
ani = animation.ArtistAnimation(fig, ims, interval=1000, repeat_delay=1000, blit=True)

HTML(ani.to_jshtml())

# Plotting the images

# Grab a batch of real images from the dataloader
real_batch = next(iter(dataloader))

# Plot the real images
plt.figure(figsize=(15,15))
plt.subplot(1,2,1)
plt.axis("off")
plt.title("Real Images")
plt.imshow(np.transpose(vutils.make_grid(real_batch[0].to(device)[:64], padding=5, normalize=True).cpu(),(1,2,0)))

# Plot the fake images from the last epoch
plt.subplot(1,2,2)
plt.axis("off")
plt.title("Fake Images")
plt.imshow(np.transpose(img_list[98],(1,2,0))) # change index at will
plt.show()
