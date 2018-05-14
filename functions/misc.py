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

def pandas_DataFrame_to_relion_star_file():
    pass