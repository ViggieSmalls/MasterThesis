# Tools for generating TEM-Simulator input files

## scripts

`create_filtered_maps.py` : Create filtered density maps for a dose fractionated series. 
The input is a density map in mrc file format. An electron dose dependent frequency filter is applied to the map and a new output map is generated for each cumulative electron dose.

`gen_temsim_input_files.py` : Generates input files for dose fractionated series with TEM-Simulator
