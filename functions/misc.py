import pandas as pd

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


def temsim_to_relion_coordinates(coordinates_file, apix, shape=(3838,3710), **kwargs):
    topix = lambda x: x * 10 / apix  # pix
    df = pd.read_csv(coordinates_file, header=1, names=['x', 'y', 'z', 'phi', 'theta', 'psi'], delim_whitespace=True, index_col=False)

    dx, dy = shape
    cx = dx // 2
    cy = dy // 2

    rln_df = pd.DataFrame()

    rln_df['_rlnCoordinateX'] = topix(df['x']) + cx
    rln_df['_rlnCoordinateY'] = topix(df['y']) + cy
    rln_df['_rlnAngleRot']  =  df['phi']
    rln_df['_rlnAngleTilt'] =  df['theta']
    rln_df['_rlnAnglePsi']  = -df['psi']
    for key in kwargs:
        rln_df[key] = kwargs[key]

    return rln_df