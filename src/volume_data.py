import pandas as pd
from functools import reduce
from src.utils import fix_years
import gc

def get_percentile(df):
    data = df.copy()
    for column in data.columns:
        if column not in ['HTID']:
            colname = column.replace('percent_', '') + '_percentile'
            data[colname] = data[column].rank(pct=True, method = 'min')
    return data

def run_volume_data(config):
    print('Volume Data')
    print('Loading Data')
    volumes = pd.read_csv(config['temporary_path'] + 'volumes.csv')
    scores = pd.read_csv(config['temporary_path'] + 'sentiment_scores.csv')
    metadata = pd.read_csv(config['temporary_path'] + 'metadata.csv')

    print('Calculating Additional Scores')
    scores['net_optimism_score'] = scores['percent_optimistic'] + scores['percent_progress_original'] - scores['percent_pessimism'] - scores['percent_regression']
    scores['progress_regression_original'] = scores['percent_progress_original'] - scores['percent_regression']
    scores['progress_regression_main'] = scores['percent_progress_main'] - scores['percent_regression']
    scores['progress_regression_secondary'] = scores['percent_progress_secondary'] - scores['percent_regression']

    print('Getting Percentiles')
    scores_percentiles = get_percentile(scores)

    print('Merging Data')
    dfs = [metadata, volumes, scores_percentiles]
    volumes_scores = reduce(lambda left,right: pd.merge(left, right, on = 'HTID', how = 'inner'), dfs) #merge on volume ID

    print('Merge Dimensions:' + str(volumes_scores.shape))

    #drop NA's and duplicates
    volumes_scores = volumes_scores.dropna()
    volumes_scores = volumes_scores.drop_duplicates()
    # volumes_scores = fix_years(volumes_scores)

    print('Exporting Data')
    volumes_scores.to_csv(config['temporary_path'] + 'volumes_scores.csv', index=False)

    del volumes, scores, metadata, scores_percentiles, volumes_scores
    gc.collect()
