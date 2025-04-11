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

    # #fix some HTIDs
    # volumes['HTID'] = volumes['HTID'].str.replace(r'[xt]$', '', regex=True)
    # metadata['HTID'] = metadata['HTID'].str.replace(r'[xt]$', '', regex=True)

    print('Merging Data')
    dfs = [metadata, volumes, scores_percentiles]
    volumes_scores = reduce(lambda left,right: pd.merge(left, right, on = 'HTID', how = 'inner'), dfs) #merge on volume ID

    print('Metadata Dimensions:' + str(metadata.shape))
    print('Volumes Dimensions:' + str(volumes.shape))
    print('Scores Dimensions:' + str(scores_percentiles.shape))
    print('Merge Dimensions:' + str(volumes_scores.shape))

    #find htids that did not merge
    missing_htids = (set(volumes['HTID']) | set(scores['HTID']) | set(metadata['HTID'])) - set(volumes_scores['HTID'])
    unmerged = pd.DataFrame(list(missing_htids), columns=['HTID'])
    unmerged['in_topics_data'] = unmerged['HTID'].isin(volumes['HTID'])
    unmerged['in_sentiment_scores_data'] = unmerged['HTID'].isin(scores['HTID'])
    unmerged['in_metadata'] = unmerged['HTID'].isin(metadata['HTID'])

    #drop duplicates
    volumes_scores = volumes_scores.drop_duplicates(subset=['HTID'])
    # volumes_scores = fix_years(volumes_scores)
    print('Merge Dimensions after dropping duplicates:' + str(volumes_scores.shape))

    print('Exporting Data')
    volumes_scores.to_csv(config['temporary_path'] + 'volumes_scores.csv', index=False)
    unmerged.to_csv(config['temporary_path'] + 'unmerged.csv', index=False)

    del volumes, scores, metadata, scores_percentiles, volumes_scores
    gc.collect()
