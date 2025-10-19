import subprocess
from src.clean_data import run_clean_data
from src.utils import load_config
from src.cross_topics import run_cross_topics
from src.categories import run_categories
from src.shares import run_shares
from src.topic_volume_weights import run_topic_volume_weights
from src.volume_data import run_volume_data
from src.figures import run_figures
from src.utils import create_r_config

def rerun_corners(config):
    """Re-runs the part of the analysis where alternative corners are used"""
    run_topic_volume_weights(config)
    run_volume_data(config)
    run_figures(config)
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])

def run_main_analysis():
    """Runs the entire analysis pipeline for the expanded and trimmed dataset, including alternative corners"""

    config = load_config('configs/config_main_analysis.yaml')

    run_clean_data(config)
    run_cross_topics(config)
    run_categories(config)
    run_shares(config)
    run_topic_volume_weights(config)
    run_volume_data(config)
    run_figures(config)
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/regression_tables.R'])
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])
    subprocess.run(['Rscript', 'Rscripts/famous_books.R'])
    subprocess.run(['Rscript', 'Rscripts/additional_ternary_figs.R'])

    # # create tables with author fixed effects

    config['author_fe'] = True
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/regression_tables.R'])
    config['author_fe'] = False

    # # create manuals figures

    config['manuals'] = True
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])
    config['manuals'] = False

    # # re-run predicted figures dropping obs before 1650

    config['min_regression_year'] = 1650
    config['output_path'] = './data/expanded_trimmed/output/drop_1650/'
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])
    config['min_regression_year'] = 1600
 
    # ###########alternative corner - economics
    config['categories'] = {
        'Religion': [10,34,38],
        'Economics': [5,45,46],
        'Science': [3,41,43]
    }

    config['output_path'] = './data/alternative_corners_economics/output/'

    print('Re-running for Economics')
    rerun_corners(config)

    # ##########alternative corner - Law

    config['categories'] = {
        'Religion': [10,34,38],
        'Law': [6,25,58],
        'Science': [3,41,43]
    }

    config['output_path'] = './data/alternative_corners_law/output/'

    print('Re-running for Law')
    rerun_corners(config)

    ###########alternative corner - Literature

    config['categories'] = {
        'Religion': [10,34,38],
        'Literature': [15,21,51],
        'Science': [3,41,43]
    }

    config['output_path'] = './data/alternative_corners_literature/output/'

    print('Re-running for Literature')
    rerun_corners(config)

if __name__ == '__main__':

    run_main_analysis()