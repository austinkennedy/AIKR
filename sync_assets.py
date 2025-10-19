import os
import shutil

from src.constants import (
    EXPANDED_TRIMMED_PATH,
    EXPANDED_TRIMMED_UNBINNED_PATH,
    ECONOMICS_PATH,
    LITERATURE_PATH,
    LAW_PATH,
    COHERENCE_PATH,
    DEST_DIR
)

def sync_assets():
    """Syncs the assets used in the paper to a dedicated folder for easier access."""

    mapping = {
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/total_volumes_raw.png'): 'fig_1',
        os.path.join(EXPANDED_TRIMMED_PATH, 'topic_triangles/grayscale'): 'fig_2',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/Political Economy.png'): 'fig_3',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/Science.png'): 'fig_3',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/Religion.png'): 'fig_3',
        os.path.join(EXPANDED_TRIMMED_PATH, 'famous_volumes_gray.png'): 'fig_4',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/avg_progress_raw.png'): 'fig_5',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_main/grayscale'): 'fig_6',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_7',
        os.path.join(ECONOMICS_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_8/economics',
        os.path.join(LAW_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_8/law',
        os.path.join(LITERATURE_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_8/literature',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/industry/grayscale'): 'fig_9',
        os.path.join(EXPANDED_TRIMMED_PATH, 'biscale_triangles'): 'fig_10',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_figures/industry_percentile/predicted_values_sci_pe.png'): 'fig_11',
        os.path.join(EXPANDED_TRIMMED_PATH, 'progress_oriented_books.csv'): 'section_6_books',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_tables/progress_main_percentile/results.tex'): 'table_b_1',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_tables/industry_percentile/results.tex'): 'table_b_4',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/total_volumes.png'): 'fig_b_1',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/corpus_vs_transl_categories.png'): 'fig_b_4',
        os.path.join(EXPANDED_TRIMMED_PATH, 'topic_triangles/color') : 'fig_b_5',
        os.path.join(EXPANDED_TRIMMED_PATH, 'famous_volumes.png'): 'fig_b_6',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/avg_progress.png'): 'fig_b_7',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_original/color'): 'fig_b_8',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_figures/progress_original_percentile/predicted_values.png'): 'fig_b_8',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_secondary/color'): 'fig_b_10',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_figures/progress_secondary_percentile/predicted_values.png'): 'fig_b_11',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_chatgpt/color'): 'fig_b_12',
        os.path.join(EXPANDED_TRIMMED_PATH, 'regression_figures/progress_chatgpt_percentile/predicted_values.png'): 'fig_b_13',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_regression_main'): 'fig_b_14',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volumes_over_time/avg_progress_translations_raw.png'): 'fig_b_16',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/progress_main/color'): 'fig_b_17',
        os.path.join(EXPANDED_TRIMMED_PATH, 'subtriangles'): 'fig_b_18',
        os.path.join(EXPANDED_TRIMMED_PATH, 'drop_1650/regression_figures/progress_main_percentile/predicted_values.png'): 'fig_b_19',
        os.path.join(EXPANDED_TRIMMED_PATH, 'drop_1650/regression_figures/progress_main_percentile/predicted_values.png'): 'fig_b_20',
        os.path.join(EXPANDED_TRIMMED_PATH, 'drop_1650/regression_figures/progress_main_percentile/predicted_values.png'): 'fig_b_20',
        os.path.join(ECONOMICS_PATH, 'volume_triangles/progress_main/grayscale'): 'fig_b_21',
        os.path.join(LAW_PATH, 'volume_triangles/progress_main/grayscale'): 'fig_b_22',
        os.path.join(LITERATURE_PATH, 'volume_triangles/progress_main/grayscale'): 'fig_b_23',
        # os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/industry_full_dict/grayscale'): 'fig_b_20/grayscale',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/industry_full_dict/color'): 'fig_b_25',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/industry/color'): 'fig_b_26',
        os.path.join(EXPANDED_TRIMMED_PATH, 'drop_1650/regression_figures/industry_percentile/predicted_values_sci_pe.png'): 'fig_b_27',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'topic_triangles/grayscale'): 'fig_e_1',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'volumes_over_time/Political Economy.png'): 'fig_e_2',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'volumes_over_time/Science.png'): 'fig_e_2',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'volumes_over_time/Religion.png'): 'fig_e_2',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'volume_triangles/progress_main/grayscale'): 'fig_e_3',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_e_4',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'volume_triangles/industry/grayscale'): 'fig_e_5',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'biscale_triangles'): 'fig_e_6',
        os.path.join(EXPANDED_TRIMMED_UNBINNED_PATH, 'regression_figures/industry_percentile/predicted_values_sci_pe.png'): 'fig_e_7',
        os.path.join(EXPANDED_TRIMMED_PATH, 'volume_triangles/optimistic'): 'fig_f_1',
        os.path.join(COHERENCE_PATH, 'volume_triangles/progress_main/color'): 'fig_c_1',
        os.path.join(COHERENCE_PATH, 'regression_figures/progress_main_percentile/predicted_values.png'): 'fig_c_2',
        os.path.join(EXPANDED_TRIMMED_PATH, 'estc_figures/estc_hathitrust_pdf.png'): 'fig_d_2',
    }

    # Remove the destination directory if it exists
    if os.path.exists(DEST_DIR):
        shutil.rmtree(DEST_DIR)

    # Create the destination directory
    os.makedirs(DEST_DIR)

    for source_path, label in mapping.items():
        dest_subfolder = os.path.join(DEST_DIR, label)
        os.makedirs(dest_subfolder, exist_ok=True)

        if not os.path.exists(source_path):
            print(f"Warning: {source_path} for {label} does not exist.")
            continue

        if os.path.isdir(source_path):
            # Copy all files and subdirs in source folder to destination folder
            for item in os.listdir(source_path):
                item_path = os.path.join(source_path, item)
                if os.path.isfile(item_path):
                    shutil.copy(item_path, dest_subfolder)
                    print(f"Copied file {item_path} -> {dest_subfolder}/")
                elif os.path.isdir(item_path):
                    shutil.copytree(item_path, os.path.join(dest_subfolder, item), dirs_exist_ok=True)
                    print(f"Copied folder {item_path} -> {dest_subfolder}/{item}/")
        else:
            # Copy a single file
            filename = os.path.basename(source_path)
            dest_path = os.path.join(dest_subfolder, filename)
            shutil.copyfile(source_path, dest_path)
            print(f"Copied {source_path} -> {dest_path}")


