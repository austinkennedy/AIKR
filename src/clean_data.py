import pandas as pd
import pickle
import gc
from functools import reduce


def clean_htids_topic_numbers(data, string_identifier):
    str_length = len(string_identifier)

    df = data.copy()
    df.drop(columns=0, inplace=True)
    df[1] = [string[string.rfind(string_identifier)+str_length:-4] for string in df[1]]
    df.columns = ['HTID'] + [i for i in range(1,len(df.columns))]
    return df

def fix_htid(row):
    return row['HTID'].replace(":","+").replace("/", "=")

def run_clean_data_baseline(config):
    """Performs data cleaning for baseline version."""

    print('Importing Data')
    topic_data = pd.read_csv(config['input_path'] + '20191007_topics.txt', sep = '\t', lineterminator = '\n', header = None)
    topic_keys = pd.read_csv(config['input_path'] + '20191007_keys.txt', sep = '\t', lineterminator='\n', header=None)

    metadata = pickle.load(open(config['input_path'] + 'metadata.p', 'rb'))
    industry = pd.read_csv(config['input_path'] + 'industry_scores.csv')
    industry_pre_1643 = pd.read_csv(config['input_path'] + 'industry_scores_updated.csv')
    sentiment = pd.read_csv(config['input_path'] + 'sentiment_scores_march23.csv')
    updated_progress = pd.read_csv(config['input_path'] + 'updated_progress_scores.csv')

    print('Cleaning Data')
    topic_data_cleaned = clean_htids_topic_numbers(data = topic_data, string_identifier='/UK_data/')

    #fix topic numbers
    topic_keys.drop(columns=0, inplace=True)
    topic_keys['topic_number'] = list(range(1,len(topic_keys)+1))
    topic_keys.columns = ['weight', 'words', 'topic_number']

    metadata['Year_rounded'] = pd.to_numeric(metadata['Year'])
    metadata['Year'] = pd.to_numeric(metadata['Year'], downcast='signed')
    metadata['HTID'] = metadata.apply(fix_htid, axis=1)
    translations = pd.read_csv(config['input_path'] + 'translations.csv')
    metadata = metadata.merge(translations, on= 'HTID', how = 'left')

    industry = industry.rename(columns={'Unnamed: 0': 'HTID', '2-vote':'industry_2','3-vote':'industry_3'})
    industry_pre_1643 = industry_pre_1643.rename(columns={'Industrial Scores (May 24)': 'industry_1643'})
    industry['HTID'] = industry['HTID'].map(lambda x: x.rstrip('.txt'))#remove '.txt' at the end of each string for HTIDs
    industry_pre_1643['HTID'] = industry_pre_1643['HTID'].map(lambda x: x.rstrip('.txt'))#remove '.txt' at the end of each string for HTIDs
    sentiment = sentiment.rename(columns = {'Unnamed: 0': 'HTID', 'Regression': 'percent_regression', 'Pessimism': 'percent_pessimism', 'Optimism':'percent_optimistic', 'Progress': 'percent_progress_original'})
    sentiment['HTID'] = sentiment['HTID'].map(lambda x: x.rstrip('.txt')) #remove '.txt' at the end of each string for HTIDs
    #NEED TO CHANGE IF YOU WANT TO INCORPORATE DIFFERENT PROGRESS SCORES
    sentiment['optimism_score'] = sentiment['percent_optimistic'] + sentiment['percent_progress_original'] - sentiment['percent_pessimism'] - sentiment['percent_regression']
    updated_progress = updated_progress.rename(columns={'Unnamed: 0': 'HTID', 'Main': 'percent_progress_main', 'Secondary': 'percent_progress_secondary'})
    updated_progress['HTID'] = updated_progress['HTID'].map(lambda x: x.rstrip('.txt'))

    sentiment_dfs = [industry, industry_pre_1643, sentiment, updated_progress]
    print('Sentiment Dimensions:' + str(sentiment.shape))
    print('Industry Dimensions:' + str(industry.shape))
    print('Updated Progress Dimensions:' + str(updated_progress.shape))
    print('Updated Industry Dimensions:' + str(industry_pre_1643.shape))

    sentiment_scores_all = reduce(lambda left,right: pd.merge(left, right, on = 'HTID', how = 'inner'), sentiment_dfs) #merge on volume ID

    print('Merged Dimensions:' + str(sentiment_scores_all.shape))

    print('Exporting Data')
    topic_data_cleaned.to_csv(config['temporary_path'] + 'topic_weights.csv', index = False)
    topic_keys.to_csv(config['temporary_path'] + 'topics.csv', index = False)
    metadata.to_csv(config['temporary_path'] + 'metadata.csv', index=False)
    sentiment_scores_all.to_csv(config['temporary_path'] + 'sentiment_scores.csv', index=False)

    del topic_data, topic_keys, metadata, topic_data_cleaned, translations, industry, industry_pre_1643, sentiment, updated_progress, sentiment_scores_all
    gc.collect()

def run_clean_data_expanded_trimmed(config):
    print('Importing Data')
    topic_data = pd.read_csv(config['input_path'] + 'LDA_01_topics.txt', sep = '\t', lineterminator = '\n', header = None)
    topic_keys = pd.read_csv(config['input_path'] + 'LDA_01_keys.txt', sep = '\t', lineterminator='\n', header=None)
    metadata = pd.read_csv(config['input_path'] + 'metadata_march25.csv')
    sentiment = pd.read_csv(config['input_path'] + 'sentiment_results_march25.csv')
    updated_progress = pd.read_csv(config['input_path'] + 'updated_progress_scores_march25.csv')
    industry = pd.read_csv(config['input_path'] + 'industry_scores_jan2025.csv')

    topic_data_cleaned = clean_htids_topic_numbers(data = topic_data, string_identifier='/Cleaned_Nov2024/')

    #fix topic numbers
    topic_keys.drop(columns=0, inplace=True)
    topic_keys['topic_number'] = list(range(1,len(topic_keys)+1))
    topic_keys.columns = ['weight', 'words', 'topic_number']

    metadata = metadata.rename(columns={'Unnamed: 0': 'HTID', 'year': 'Year'})
    metadata['Year_rounded'] = pd.to_numeric(metadata['Year'])
    metadata['Year'] = pd.to_numeric(metadata['Year'], downcast='signed')
    metadata['HTID'] = metadata.apply(fix_htid, axis=1)

    sentiment = sentiment.rename(columns = {'Unnamed: 0': 'HTID', 'Regression': 'percent_regression', 'Pessimism': 'percent_pessimism', 'Optimism':'percent_optimistic', 'Progress': 'percent_progress_original'})
    sentiment['HTID'] = sentiment['HTID'].map(lambda x: x.rstrip('.txt')) #remove '.txt' at the end of each string for HTIDs
    #NEED TO CHANGE IF YOU WANT TO INCORPORATE DIFFERENT PROGRESS SCORES
    sentiment['optimism_score'] = sentiment['percent_optimistic'] + sentiment['percent_progress_original'] - sentiment['percent_pessimism'] - sentiment['percent_regression']


    updated_progress = updated_progress.rename(columns={'Unnamed: 0': 'HTID', 'Main': 'percent_progress_main', 'Progress': 'percent_progress_secondary'})
    updated_progress['HTID'] = updated_progress['HTID'].map(lambda x: x.rstrip('.txt'))

    industry = industry.rename(columns={'Unnamed: 0': 'HTID', 'Industrial Scores (June 23)':'industry'})
    industry['HTID'] = industry['HTID'].map(lambda x: x.rstrip('.txt'))#remove '.txt' at the end of each string for HTIDs

    sentiment_dfs = [industry, sentiment, updated_progress]

    print('Sentiment Dimensions:' + str(sentiment.shape))
    print('Industry Dimensions:' + str(industry.shape))
    print('Updated Progress Dimensions:' + str(updated_progress.shape))

    sentiment_scores_all = reduce(lambda left,right: pd.merge(left, right, on = 'HTID', how = 'inner'), sentiment_dfs) #merge on volume ID

    print('Merged Dimensions:' + str(sentiment_scores_all.shape))

    #drop NAs
    topic_data_cleaned = topic_data_cleaned.dropna()
    sentiment_scores_all = sentiment_scores_all.dropna()

    print('Exporting Data')
    topic_data_cleaned.to_csv(config['temporary_path'] + 'topic_weights.csv', index = False)
    topic_keys.to_csv(config['temporary_path'] + 'topics.csv', index = False)
    metadata.to_csv(config['temporary_path'] + 'metadata.csv', index=False)
    sentiment_scores_all.to_csv(config['temporary_path'] + 'sentiment_scores.csv', index=False)

    del topic_data, topic_keys, metadata, topic_data_cleaned, sentiment, updated_progress, industry, sentiment_scores_all
    gc.collect()
    


def run_clean_data(config):

    if config['version'] == 'baseline':
        run_clean_data_baseline(config)
    if config['version'] == 'expanded_trimmed':
        run_clean_data_expanded_trimmed(config)