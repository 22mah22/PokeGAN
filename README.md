# PokeGAN
Trying to generate pokemon sprites using a DCGAN

For now, using torch default implementation for a DCGAN on approximately 5000 sprites from pokemon games in generations 3,4,5.
Default implementation only creates noise.

Problem: The default implementation only manages to generate noise
Reason: The Discriminator very quickly manages to sort all samples correctly which bottlenecks the Generator's training.

Potential issues to try and remedy:
- Sample size is limited to ~5000 pictures where many are similar or only have color differences. 
- There are around 500 different species of pokemon in the database. Some have more (different) sprites available than others.
  - This should probably have an impact on batch sizing and number of iterations. 
