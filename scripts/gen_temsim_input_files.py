import os
from string import Template
import pandas as pd
import random
import numpy as np
import math
import pickle

error_file_template = Template("""1  5
#            rho             alpha             tau           x         y
             0               0                 0             ${x}      ${y}
""")

temsim_input_template = Template("""
=== simulation ===

generate_micrographs = yes
log_file                                    = ${log_file}
rand_seed                                   = ${rand_seed}

=== sample ===

diameter 									= 100000
thickness_center = 50
thickness_edge = 50

=== electronbeam ===

acc_voltage = 300
energy_spread = 0.7
gen_dose = yes
total_dose 									= ${dose_per_frame}
dose_sd = 0

=== geometry ===

gen_tilt_data = yes
ntilts = 1
theta_start = 0
theta_incr = 0
geom_errors                                 = ${geom_errors}
error_file_in                               = ${error_file_in}

=== optics ===

magnification 								= ${magnification}
cs = 2.62
cc = 2.62
aperture = 100
focal_length = 3.5
cond_ap_angle = 0.03
gen_defocus = yes
defocus_nominal                             = ${defocus}
phase_shift                                 = ${phase_shift}
phase_plate_spot = 0.050000

=== detector ===

det_pix_x 									= ${det_pix_x}
det_pix_y 									= ${det_pix_y}
padding = 50
pixel_size                                  = ${det_pixel_size}
gain = 1
use_quantization = no
dqe = 1
mtf_a = 0
mtf_b = 0
mtf_c = 1
mtf_alpha = 0
mtf_beta = 0
image_file_out                              = ${output_no_noise}

=== detector ===

det_pix_x 									= ${det_pix_x}
det_pix_y 									= ${det_pix_y}
padding = 50
pixel_size                                  = ${det_pixel_size}
gain = 1
use_quantization = yes
dqe = 1
mtf_a = 0
mtf_b = 0
mtf_c = 1
mtf_alpha = 0
mtf_beta = 0
image_file_out                              = ${output_with_noise}

""")

particle_input_template = Template("""
=== particle ${name} ===

source = map
map_file_re_in                              = ${map_file_re_in}
voxel_size                                  = ${voxel_size}
use_imag_pot = no
famp = 0.1
randomize_particle                          = ${randomize_particle}
rand_seed_particle                          = ${rand_seed_particle}

=== particleset ===

particle_type                               = ${name}
particle_coords = file
coord_file_in                               = ${coordinates}
""")


def gen_geometry_errors(n_frames, max_drift_dist=1, decay_dist_variance=-0.1, max_angle_variance=math.pi / 4,
                        decay_angle_variance=-0.4) -> list:
    """
    simulates the new x and y position of the frame center
    as an effect of beam induced movement
    the drift distance exponentially drops off
    the drift angle is dependent on the previous drift angle
    and the angular variation also drops off exponentially
    :param max_drift_dist: in nm
    :return: [ (x1,y1), (x2,y2), ... ]
    """
    x = [0]
    y = [0]
    deg = [random.random() * math.pi * 2]  # initial drift angle

    for i in range(n_frames - 1):
        last_deg = deg[-1]
        last_x_pos = x[-1]
        last_y_pos = y[-1]
        deg_var = math.exp(decay_angle_variance * i) * max_angle_variance
        new_deg = random.uniform(last_deg - deg_var, last_deg + deg_var)
        rand_dist = random.random() * math.exp(decay_dist_variance * i) * max_drift_dist
        new_x_pos = math.cos(new_deg) * rand_dist + last_x_pos
        new_y_pos = math.sin(new_deg) * rand_dist + last_y_pos
        x.append(new_x_pos)
        y.append(new_y_pos)
        deg.append(new_deg)

    return list(zip(x, y))


def relion_star_file_to_DataFrame(path):
    cnt = 0
    df_columns = []

    with open(path) as star_file:
        for line in star_file:
            stripped_line = line.strip()
            if stripped_line.startswith("data_") or stripped_line.startswith("loop_") or stripped_line == "":
                cnt += 1
            elif stripped_line.startswith("_"):
                df_columns.append(stripped_line.split()[0])
                cnt += 1
            else:
                break
        star_file.close()

    return pd.read_csv(path, skiprows=cnt, delim_whitespace=True, names=df_columns)


def pandas_DataFrame_to_relion_star_file(df, out_star):
    with open(out_star, 'w') as f:
        f.write('data_\nloop_\n')
        rln_cols = []
        for col in df.columns:
            if col.startswith('_rln'):
                f.write(col + '\n')
                rln_cols.append(col)
        df[rln_cols].to_csv(f, header=False, index=False, sep='\t')


def write_temsim_coordinates(df, file_out):
    header_template = Template(
        "${ROWS}  6\n"
        "#            x             y             z           phi         theta           psi\n"
    )
    with open(file_out, "w") as f:
        f.write(header_template.substitute(ROWS=len(df)))
        rows = df[['x', 'y', 'z', 'phi', 'theta', 'psi']]
        rows.to_csv(f, header=False, sep='\t', index=False)

def save_random_state(filename):
    random_state = np.random.get_state()
    pickle.dump(random_state, open(filename, "wb"))

def load_random_state(filename):
    random_state = pickle.load( open( filename , "rb" ) )
    np.random.set_state(random_state)

def main(outp_dir, angles_star, n_frames,
         simulate_drift, dose, voxelsize,
         struct, filtered_maps_dir, max, rand):

    if rand is not None:
        if os.path.isfile(rand):
            load_random_state(rand)
        else:
            save_random_state(rand)

    star_file = angles_star
    BASE_DIR = outp_dir

    # micrograph parameters
    n_frames = n_frames
    dose_per_frame = dose / n_frames

    det_pix_x = 3838
    det_pix_y = 3710

    print('Output directory:', BASE_DIR)
    print('Angles star file:', star_file)
    print('Number of frames:', n_frames)
    print('Dose per frame:', dose_per_frame)
    print('Simulate drift:', simulate_drift)
    print('Structural noise:', True if struct is not None else False)

    if input('Do you wish to proceed with these values?\n') in ('y', 'yes'):
        print('Continuing...')

        # read content of the input star file
        ptcls_star_content = relion_star_file_to_DataFrame(star_file)
        # create an empty DataFrame to store coordinated of particles and details of the simulated micrographs
        output_particles_df = pd.DataFrame()


        dose_array = np.append(np.array(0), np.cumsum(np.repeat(dose_per_frame, n_frames - 1)))

        if max < 0:
            micrograph_names = ptcls_star_content['_rlnMicrographName'].unique()
        else:
            micrograph_names = ptcls_star_content['_rlnMicrographName'].unique()[:max]
        for micrograph in micrograph_names:
            basename = os.path.splitext(os.path.basename(micrograph))[0]
            OUTPUT_DIR = os.path.join(BASE_DIR, basename)
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            # select all rows and columns with this micrograph name
            micrograph_df = ptcls_star_content.loc[ptcls_star_content['_rlnMicrographName'] == micrograph].copy()
            # change the micrograph name to match the future location of the simulated micrographs
            micrograph_df['_rlnMicrographName'] = os.path.join(BASE_DIR, basename + '.mrc')
            micrograph_df['_rlnParticleId'] = range(len(output_particles_df), len(output_particles_df) + len(micrograph_df))


            # read defocus value from star file
            defocus = ( float(micrograph_df['_rlnDefocusU'].unique()) + float(micrograph_df['_rlnDefocusV'].unique()) ) / 2e4  # µm
            # read phase shift from star file.
            # Decrease dose per frame because of loss of electrons through scattering by the phase plate
            if '_rlnPhaseShift' in micrograph_df.columns:
                phase_shift = float(micrograph_df['_rlnPhaseShift'].unique())
                dose_per_frame *= 0.9
            else:
                phase_shift = 0
            # read detector parameters from star file
            magnification = float(micrograph_df['_rlnMagnification'].unique())
            det_pixel_size = float(micrograph_df['_rlnDetectorPixelSize'].unique())
            pixel_size_image = det_pixel_size / magnification * 10000  # A/pix

            if simulate_drift:
                errors = gen_geometry_errors(n_frames)
                with open(os.path.join(OUTPUT_DIR, "drift.txt"), "w") as f:
                    f.write("\n".join(["{}\t{}".format(x, y) for x, y in errors]))
            else:
                errors = None

            df = pd.DataFrame()
            df['x'] = (micrograph_df['_rlnCoordinateX'] - det_pix_x // 2) * pixel_size_image / 10
            df['y'] = (micrograph_df['_rlnCoordinateY'] - det_pix_y // 2) * pixel_size_image / 10
            df['z'] = 0
            df['psi']   = -micrograph_df['_rlnAnglePsi'].astype(float)
            df['theta'] = -micrograph_df['_rlnAngleTilt'].astype(float)
            df['phi']   = -micrograph_df['_rlnAngleRot'].astype(float)

            if simulate_drift:
                fmref = n_frames // 2  # reference frame for motioncor is by default the middle frame
                error_x, error_y = errors[fmref]  # nm
                micrograph_df['_rlnOriginX'] = - error_x * 10 / pixel_size_image
                micrograph_df['_rlnOriginY'] = - error_y * 10 / pixel_size_image

            output_particles_df = output_particles_df.append(micrograph_df)

            coordinates_file = os.path.join(OUTPUT_DIR, "coordinates.txt")
            write_temsim_coordinates(df, coordinates_file)

            # write input files
            for n in range(n_frames):
                input_file = os.path.join(OUTPUT_DIR, "input_frame_{}.txt".format(str(n).zfill(2)))
                error_file = os.path.join(OUTPUT_DIR, "error_frame_{}.txt".format(str(n).zfill(2)))

                content_input = temsim_input_template.substitute(
                    log_file=os.path.join(OUTPUT_DIR, "simulation_frame_{:02d}.log".format(n)),
                    rand_seed=np.random.randint(10000),
                    output_no_noise=os.path.join(OUTPUT_DIR, "frame_{:02d}_no_noise.mrc".format(n)),
                    output_with_noise=os.path.join(OUTPUT_DIR, "frame_{:02d}_with_noise.mrc".format(n)),
                    defocus=defocus,
                    phase_shift=phase_shift,
                    magnification=magnification,
                    det_pixel_size=det_pixel_size,
                    det_pix_x=det_pix_x,
                    det_pix_y=det_pix_y,
                    dose_per_frame=dose_per_frame * 100,  # e/nm²
                    geom_errors='none' if errors is None else 'file',
                    error_file_in='none' if errors is None else error_file
                )

                # check if particle component exists
                filtered_map_file = os.path.join(os.path.abspath(filtered_maps_dir),
                                                 "filt_{:5.3f}.mrc".format(dose_array[n]))
                assert os.path.isfile(filtered_map_file)
                particle_input = particle_input_template.substitute(
                    map_file_re_in=filtered_map_file,
                    coordinates=coordinates_file,
                    voxel_size=voxelsize / 10,  # nm
                    randomize_particle='no',
                    rand_seed_particle=0,  # has no effect
                    name='proteasome'
                )

                with open(input_file, "w") as f:
                    f.write(content_input)
                    f.write(particle_input)
                    if struct is not None:

                        coords_struct_file = os.path.join(OUTPUT_DIR, "single_coordinate.txt")

                        with open(coords_struct_file,'w') as coords_struct:
                            coords_struct.write("1  6\n")
                            coords_struct.write("#            x             y             z           phi         theta           psi\n")
                            coords_struct.write("        0.0000       0.0000        0.0000              0           0               0\n")

                        struct_input = particle_input_template.substitute(
                            map_file_re_in=struct,
                            coordinates=coords_struct_file,
                            voxel_size=0.1,
                            randomize_particle='yes',
                            rand_seed_particle=abs(hash(micrograph)),
                            name='struct'
                        )
                        f.write(struct_input)

                if simulate_drift:
                    with open(error_file, "w") as f:
                        f.write(error_file_template.substitute(x=errors[n][0], y=errors[n][1]))

        output_star_file = os.path.join(BASE_DIR, 'particles.star')
        # as long as a file with this name exists, ask for a new file name
        while os.path.isfile(output_star_file):
            new_name = input('A file with the name "{}" already exists in the output folder. '
                             'Enter a new name:\n'.format(os.path.basename(output_star_file)))
            output_star_file = os.path.join(BASE_DIR, new_name)
        pandas_DataFrame_to_relion_star_file(output_particles_df, output_star_file)



if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Create TEM-Simulator input files from a relion star file. "
                                                 "Mandatory columns in the star file are: "
                                                 "['_rlnCoordinateX', '_rlnCoordinateY', '_rlnAnglePsi', '_rlnAngleRot', "
                                                 "_rlnAngleTilt', '_rlnMicrographName', '_rlnDefocusU', "
                                                 "_rlnDefocusV', '_rlnPhaseShift', '_rlnMagnification', "
                                                 "_rlnDetectorPixelSize']")
    parser.add_argument('--o', type=str, default=os.path.abspath(os.curdir),
                        help='Output directory for the input files')
    parser.add_argument('--angles', type=str, default=None,
                        help='particles.star file with angles and coordinates')
    parser.add_argument('--fmaps', type=str, default=os.path.abspath(os.curdir),
                        help='Directory which contains filtered maps. Default is current directory')
    parser.add_argument('--dose', type=float, default=30,
                        help='Total electron dose for micrograph, in e/A². Default = 30')
    parser.add_argument('--frames', type=int, default=1,
                        help='Number of frames. Default = 1')
    parser.add_argument('--max', type=int, default=1,
                        help='Maximum number of micrographs to create input files for. Use a negative value to simulate all micrographs. Default = 1')
    parser.add_argument('--drift', action='store_true', default=False,
                        help='Use this option to simulate drift as movement of the whole frame. Default is no drift')
    parser.add_argument("--struct", type=str, default=None,
                        help='MRC file that will be used as structural noise')
    parser.add_argument('--voxelsize', type=float, default=1.0,
                        help='Voxel size of the input particle map in Angstrom. Default = 1')
    parser.add_argument('--rand', type=str, default=None,
                        help='Input/Output random state file. If file already exists, the random seed for numpy is set. '
                             'If file does not exist, it is created and the random state of the simulation is saved.')

    args = parser.parse_args()

    main(
        outp_dir=args.o,
        angles_star=args.angles,
        n_frames=args.frames,
        simulate_drift=args.drift,
        dose=args.dose,
        struct=args.struct,
        filtered_maps_dir=args.fmaps,
        voxelsize=args.voxelsize,
        max=args.max,
        rand = args.rand
    )

