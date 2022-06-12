# PokeGAN
A generative adversarial network that uses a dataset of 64x64 pokemon sprites to generate new pokemon-looking pictures.

How to run:
- Download the datset using the script "pokemon_dl.py". 
- The dataset is downloaded to the directory of your choice as specified by the parameter "POKEDIR". 
- Resize the dataset to 64x64 using the script "resize.py".
- Make sure the placement of the dataset is consistent with the parameter "dataroot" in DCGAN_main.py. This can be either an regular folder or a folder in Google Drive for Colab usage. 
- Run the file "DCGAN_main.py".
