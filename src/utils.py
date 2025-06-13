import yaml
import os

def load_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

def make_dir(path):
    #check if directory in path exists, if not create it
    if not os.path.exists(path):
        print('Creating directory: ' + path)
        os.makedirs(path)
    else:
        print('Directory already exists: ' + path)

def fix_years(df):
    for ind,row in df.iterrows():
        if row['Year'] > 1890:
            df.at[ind, 'Year'] = 1890
        elif row['Year'] < 1510:
            df.at[ind, 'Year'] = 1510

    return df

def create_r_config(config, config_path):
    """Creates a config YAML file for R"""

    print('Creating R config file: ' + config_path)

    config['category_names'] = list(config['categories'].keys())

    config['author_fe'] = config.get('author_fe', False)

    with open(config_path, 'w') as f:
        yaml.dump(config, f, sort_keys=False)


        