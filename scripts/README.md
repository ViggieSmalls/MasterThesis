# Scripts for data simulation

Use `--help` for full parameter descriptions

## `create_filtered_maps.py`

Apply radiation damage to an input scattering potential map. The radiation damage is modeled as a dose and frequency 
dependent low pass filter. The frequency decay is based on measurements made by 

> *Grant, Timothy and Grigorieff, Nikolaus*: Measuring the optimal exposure for single particle cryo-EM using a 2.6 Å reconstruction of rotavirus VP6

#### Example:

    python create_filtered_maps.py input_map.mrc dir_filtered_maps --voxelsize 1 --dose 39 --nf 24 --factor 1

## `gen_particles_star.py`

Creates a star file where particles are positioned on a grid and the euler angles are either randomly selected within the 
specified interval or are read from a star file. 

#### Example:

    python gen_particles_star.py output_particles.star --mics 5 --np 5 5 --pd 30 --apix 1 --defocus 0.8 1.7
    
## `gen_temsim_input_files.py`

Takes a particles star file and a folder with damage filtered input maps and generates TEM-Simulator input files.

#### Example:

    python gen_temsim_input_files.py --o output_dir --angles particle.star --fmaps dir_filtered_maps --dose 39 --frames 24 --max 2
    
## `radial_profile.py`

Create radial profile of input micrographs and plot output. The power spectrum is computed for 512x512 patches. 
By default the results are written to `profiles.csv`. 

#### Example:

    python radial_profile.py *.mrc