from main_analysis import run_main_analysis
from unbinned_analysis import run_unbinned_analysis
from coherence import run_coherence
from pre_1800 import run_pre_1800
from sync_assets import sync_assets

if __name__ == "__main__":

    run_main_analysis()
    run_unbinned_analysis()
    run_pre_1800()
    run_coherence()
    sync_assets()