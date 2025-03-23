from src.clean_data import run_clean_data
from src.utils import load_config
from src.cross_topics import run_cross_topics
from src.categories import run_categories
from src.shares import run_shares

def main_baseline():

    config = load_config('configs/config_baseline.yaml')

    # run_clean_data(config)
    # run_cross_topics(config)
    # run_categories(config)
    run_shares(config)


if __name__ == '__main__':

    main_baseline()