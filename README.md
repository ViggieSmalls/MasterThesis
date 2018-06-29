# Tutorial for simulating micrographs with TEM-Simulator

#### Requirements

Python version: 3

Python libraries:
 
    numpy
    pandas
    matplotlib
    mrcfile 

## 1. Download and compile TEM-Simulator

    git clone https://github.com/ViggieSmalls/TEM-Simulator
    cd TEM-Simulator
    cmake CMakeLists.txt 
    make
    # set a variable to the path of the executable, we will need it later 
    TEM-Simulator=$PWD/TEM-Simulator

## 2. Create input map

Download the scripts and example input files for TEM-Simulator  
    
    git clone https://github.com/ViggieSmalls/MasterThesis
    
The file `MasterThesis/input_files/gen_map.txt` will be used as input for TEM-Simulator to generate 
a scattering potential map. This map will be filtered with the *damage_filter* to produce input maps for 
every frame of the dose fractionated series.

Change the voxel size of the output scattering potential map in the `MasterThesis/input_files/gen_map.txt` file 
to 0.1 (nm) and set the option `add_hydrogen = yes`.

    ...
    add_hydrogen = yes
    voxel_size = 0.1
    ...
    
The component `=== electornbeam ===` only has an influence on the absorption potential, so changes here 
will not influence the real part of the scattering potential.

Now change the directory to the input file and launch TEM-Simulator with `gen_map.txt` as input.
    
    cd MasterThesis/input_files
    $TEM-Simulator gen_map.txt
    
This should produce the log file and the output map.
    
## 3. Apply the *damage filter* on the input map

A script for creating damage filtered maps for a dose fractionated series can be found in `scripts`. 
`create_filtered_maps.py` takes a scattering potential map as input and generates filtered maps, based on the dose 
per frame and voxel size of the map. Use `--help` to list all the options and parameter descriptions.

Let's create filtered maps, matching the VPP with defocus data (EMPIAR-10078), with a total dose of 39 e/A² and 
24 frames. The parameter `--factor 1` is the empirical factor used to decrease the intensity of the scattering potential 
due to the fine sampling. 

    cd ..
    python scripts/create_filtered_maps.py input_files/map.mrc factor1_maps --voxelsize 1 --dose 39 --nf 24 --factor 1
    # type 'y' or 'yes' to continue
    
This will create the `factor1_maps` directory and write the filtered maps inside it.

    $ ls factor1_maps
    filt_0.000.mrc   filt_14.625.mrc  filt_17.875.mrc  filt_22.750.mrc  filt_27.625.mrc  filt_32.500.mrc  filt_35.750.mrc  filt_6.500.mrc
    filt_11.375.mrc  filt_16.250.mrc  filt_19.500.mrc  filt_24.375.mrc  filt_29.250.mrc  filt_3.250.mrc   filt_37.375.mrc  filt_8.125.mrc
    filt_13.000.mrc  filt_1.625.mrc   filt_21.125.mrc  filt_26.000.mrc  filt_30.875.mrc  filt_34.125.mrc  filt_4.875.mrc   filt_9.750.mrc

## 4. Simulate micrograps

In order to simulate a dose fractionated series, we need to simulate one frame at a time, since we use 
different input maps for every frame because of the applied damage filter. Most of the parameters remain the same for all 
frames, such as electron beam parameters, optics parameters, detector parameters, etc. Here is a list 
of parameters that need to be changed for every frame/micrograph:

    === simulation ===
    log_file: Every frame has a separate log file
    rand_seed: This parameter is VERY important for dose fractionated series. It specifies 
               the random seed for the shot noise. Each frame should have a different random seed,
               otherwise averaging the frames will produce noise artefacts
    
    === geometry ===
    geom_errors: This is used to simulate frame drift. Every frame needs a separate error file, 
                 defined by the error_file_in parameter
    error_file_in: Path to file
    
    === detector ===
    image_file_out: Path to output mrc file of the frame/micrograph

The folder `scripts` contains two scripts that greatly simplify the generation of TEM-Simulator input files. 
The script `gen_temsim_input_files.py` generates the input files, based on an input star file. 
The star file must contain following columns:

    ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnAnglePsi', '_rlnAngleRot', '_rlnAngleTilt', '_rlnMicrographName', '_rlnDefocusU', _rlnDefocusV', '_rlnPhaseShift', '_rlnMagnification', _rlnDetectorPixelSize']

The easiest way to provide such a star file is by simply taking a relion `*_data.star` file of a 3D classification. Such a 
star file (excerpt) can be found in `input_files/run_it025_data.star`. Use the parameter `--max` to specify the number of micrographs 
that will be simulated (a negative values simulates all micrographs in the star file). Also don't forget to use 
`--help` first, to see all available parameters. 

    mkdir factor1_simulations
    python scripts/gen_temsim_input_files.py -o factor1_simulations/ --angles input_files/run_it025_data.star --fmaps factor1_maps/ --dose 39 --frames 24 --max 5 --voxelsize 1
    
The output directory will contain the micrograph folders and a `particles.star` file.

    $ ls factor1_simulations
    20S_001_Mar28_14.59.32  20S_003_Mar28_15.07.18  20S_004_Mar28_15.09.38  20S_005_Mar28_15.11.58  20S_006_Mar28_15.14.18  particles.star
    
The `particles.star` file can be used later in Relion, to import the particles. If simulation includes drift, 
then two additional columns will be added `['_rlnOriginX', '_rlnOriginY']` that specify the particle position in the 
middle frame. This is the default frame used as reference by Motioncor2.

Also a column called `_rlnParticleId` will be added, to trace the particles during the refinements.

You can write a `commands.txt` file for executing all commands. Assuming you saved the path to the TEM-Simulator 
executable to the variable `$TEM-Simulator`, you can do:

    for d in `find factor1_simulations -maxdepth 1 -mindepth 1 -type d`; do for input_file in $d/input*; do echo $TEM-Simulator $input_file; done; done >> input_files.txt
    
After simulating all frames you can use a similar command to create a frame stack:

    for d in `find factor1_simulations -maxdepth 1 -mindepth 1 -type d`; do e2proc2d.py $d/*with_noise.mrc $d/stack.mrcs; done
    # average all frames
    for d in `find factor1_simulations -maxdepth 1 -mindepth 1 -type d`; do e2proc3d.py --average $d/stack.mrcs $d/average.mrc; done
    # average all, except of the first two frames
    for d in `find factor1_simulations -maxdepth 1 -mindepth 1 -type d`; do e2proc3d.py --average $d/stack.mrcs $d/average.mrc --first 2; done
    
    for d in `find factor1_simulations -maxdepth 1 -mindepth 1 -type d`; do cp $d/average_throw2.mrc $d.mrc; done
    
Now you can start relion in the current directory, import micrographs and the particles star file and start your reconstructions.

#### Generate random star file

The second way you can provide a star file for the simulations is with the script `gen_particles_star.py`. This creates 
a star file where the particles are positioned on a grid and the euler angles are either randomly selected within the 
specified interval or are read from a star file with the columns `['_rlnAnglePsi', '_rlnAngleRot', '_rlnAngleTilt']`, e.g.:

    _rlnAnglePsi
    _rlnAngleRot
    _rlnAngleTilt
    -128.0	109.58	82.26
    89.17	91.66	95.3
    -90.77	75.22	89.19
    ...
    
A new star file can be created e.g. with one of the following commands:

    python scripts/gen_particles_star.py my_star_file.star --np 10 10 --pd 30 --apix 1.06 --mics 10 --defocus 0.5 1
    python scripts/gen_particles_star.py my_star_file.star --np 10 10 --pd 30 --apix 1.06 --mics 10 --defocus 0.5 1 --ps 36 144
    python scripts/gen_particles_star.py my_star_file.star --np 10 10 --pd 30 --apix 1.06 --mics 10 --defocus 0.5 1 --ps 36 144 --rot 0 180 --tilt 0 45 --psi -180 180
    python scripts/gen_particles_star.py my_star_file.star --np 10 10 --pd 30 --apix 1.06 --mics 10 --defocus 0.5 1 --ps 36 144 --angles input_files/angles.star
    
Once you have a valid star file you can continue with the simulation as described earlier.

## 5. Additional options

### Add structural noise

`gen_temsim_input_files.py` has the option `--struct` where you can specify an MRC file to use as structural noise. 
It uses the option implemented in TEM-Simulator `randomize_particle = yes` that takes each pixel value *x* of an 
input map and converts it to a random variable between *-x* and *x* before 'placing' it inside the specimen.

This method saves you from providing different random noise maps for each micrograph. Usage example:

    python scripts/make_noise.py 100 --shape 300 400
    python scripts/gen_temsim_input_files.py [...options...] --struct flat_noise.mrc
    
Tip: you can also overlap the particles with random noise maps generated this way, e.g. to simulate radiation damage.
    
### Add drift

Adds drift as an entire shift of the frame. This generates additional geometry error files for each 
frame that are used as input for TEM-Simulator.
It also crates a `drift.txt` file with all geometry errors. 

    python scripts/gen_temsim_input_files.py [...options...] --drift
