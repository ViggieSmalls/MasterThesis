# Tools for generating TEM-Simulator input files

## Tutorial

#### Requirements

Python version: 3

Python libraries:
 
    numpy
    pandas
    matplotlib
    mrcfile 

### 1. Download and compile TEM-Simulator

    git clone https://github.com/ViggieSmalls/TEM-Simulator
    cd TEM-Simulator
    cmake CMakeLists.txt 
    make
    # set e.g. an alias for the executable
    alias TEM-Simulator='$PWD/TEM-Simulator'

### 2. Create input map

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
    TEM-Simulator gen_map.txt
    
This should produce the log file and the output map.
    
### 3. Apply the *damage filter* on the input map

A script for creating damage filtered maps for a dose fractionated series can be found in `scripts`. 
`create_filtered_maps.py` takes a scattering potential map as input and generates filtered maps, based on the dose 
per frame and voxel size of the map. Use `--help` to list all the options and parameter descriptions.

Let's create filtered maps, matching the VPP with defocus data (EMPIAR-10078), with a total dose of 39 e/A² and 
24 frames. The parameter `--factor 1` is the empirical factor used to decrease the intensity of the scattering potential 
due to the fine sampling. 

    cd ..
    python scripts/create_filtered_maps.py input_files/map.mrc factor1_maps --voxelsize 1 --dose 39 -nf 24 --factor 1
    # type 'y' or 'yes' to continue
    
This will create the `factor1_maps` directory and write the filtered maps inside it.

    $ ls factor1_maps
    filt_0.000.mrc   filt_14.625.mrc  filt_17.875.mrc  filt_22.750.mrc  filt_27.625.mrc  filt_32.500.mrc  filt_35.750.mrc  filt_6.500.mrc
    filt_11.375.mrc  filt_16.250.mrc  filt_19.500.mrc  filt_24.375.mrc  filt_29.250.mrc  filt_3.250.mrc   filt_37.375.mrc  filt_8.125.mrc
    filt_13.000.mrc  filt_1.625.mrc   filt_21.125.mrc  filt_26.000.mrc  filt_30.875.mrc  filt_34.125.mrc  filt_4.875.mrc   filt_9.750.mrc

### 4. Simulate micrograps

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

    ['_rlnCoordinateX', '_rlnCoordinateY', '_rlnAnglePsi', '_rlnAngleRot', _rlnAngleTilt', '_rlnMicrographName', '_rlnDefocusU', _rlnDefocusV', '_rlnPhaseShift', '_rlnMagnification', _rlnDetectorPixelSize']

The easiest way to provide such a star file is by simply taking a relion `*_data.star` file of a 3D classification. Such a 
star file (excerpt) can be found in `input_files/run_it025_data.star`. Use the parameter `--max` to specify the number of micrographs 
that will be simulated (a negative values simulates all micrographs in the star file). Also don't forget to use 
`--help` first, to see all available parameters. 

    mkdir factor1_simulations
    python scripts/gen_temsim_input_files.py -o factor1_simulations/ --angles input_files/run_it025_data.star --fmaps factor1_maps/ --dose 39 --frames 24 --max 5 --voxelsize 1
    
