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


def run_unbinned_analysis():
    """Runs the entire analysis pipeline for the expanded and trimmed dataset, including alternative corners"""

    config = load_config('configs/config_main_analysis.yaml')

    config['temporary_path'] = './data/expanded_trimmed_unbinned/temporary/'
    config['output_path'] = './data/expanded_trimmed_unbinned/output/'

    config['bins'] = False

    run_clean_data(config)
    run_cross_topics(config)
    run_categories(config)
    run_shares(config)
    run_topic_volume_weights(config)
    run_volume_data(config)
    run_figures(config)
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])
    subprocess.run(['Rscript', 'Rscripts/additional_ternary_figs.R'])

    # re-run predicted figures dropping obs before 1650

    config['min_regression_year'] = 1650
    config['output_path'] = './data/expanded_trimmed_unbinned/output/drop_1650/'
    create_r_config(config, 'Rscripts/r_config.yaml')
    subprocess.run(['Rscript', 'Rscripts/marginal_predicted_figs.R'])

if __name__ == "__main__":
    run_unbinned_analysis()