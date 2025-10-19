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

def run_pre_1800():
    """Runs the entire analysis pipeline for the data based on pre_1800 scores."""

    config = load_config('configs/config_pre_1800.yaml')

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

if __name__ == "__main__":
    run_pre_1800()