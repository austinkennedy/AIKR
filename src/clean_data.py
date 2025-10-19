import pandas as pd
import pickle
import gc
import re
from functools import reduce
from src.utils import make_dir
from src.constants import manual_and_related_words


def clean_htids_topic_numbers(data, string_identifier):
    str_length = len(string_identifier)

    df = data.copy()
    df.drop(columns=0, inplace=True)
    df[1] = df[1].str.split('/').str[-1].str.strip("'")
    df.columns = ['HTID'] + [i for i in range(1,len(df.columns))]
    df['HTID'] = df['HTID'].str.replace('.txt', '')
    return df

def fix_htid(row):
    return row['HTID'].replace(":","+").replace("/", "=")

def flag_words(df, colnames, words, new_colname):
    """
    Flags words in a given column of a DataFrame.

    Parameters:
    df (pd.DataFrame): The DataFrame to process.
    colname (str): The name of the column to search for words.
    words (list): A list of words to flag.
    new_colname (str): The name of the new column to create for flags.

    Returns:
    pd.DataFrame: The modified DataFrame with the new flag column.
    """
    pattern = '|'.join(map(re.escape, words))

    match_series = pd.Series(False, index=df.index)

    for colname in colnames:
        if colname not in df.columns:
            raise ValueError(f"Column '{colname}' not found in DataFrame.")
        # Create a new column with flags based on the pattern
        match_series |= df[colname].astype(str).str.contains(pattern, case=False, na=False)

    df[new_colname] = match_series.astype(int)  # Convert boolean to int (0 or 1)

    return df

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
    industry['HTID'] = industry['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs
    industry_pre_1643['HTID'] = industry_pre_1643['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs
    sentiment = sentiment.rename(columns = {'Unnamed: 0': 'HTID', 'Regression': 'percent_regression', 'Pessimism': 'percent_pessimism', 'Optimism':'percent_optimistic', 'Progress': 'percent_progress_original'})
    sentiment['HTID'] = sentiment['HTID'].map(lambda x: x.replace('.txt', '')) #remove '.txt' at the end of each string for HTIDs
    #NEED TO CHANGE IF YOU WANT TO INCORPORATE DIFFERENT PROGRESS SCORES
    sentiment['optimism_score'] = sentiment['percent_optimistic'] + sentiment['percent_progress_original'] - sentiment['percent_pessimism'] - sentiment['percent_regression']
    updated_progress = updated_progress.rename(columns={'Unnamed: 0': 'HTID', 'Main': 'percent_progress_main', 'Secondary': 'percent_progress_secondary'})
    updated_progress['HTID'] = updated_progress['HTID'].map(lambda x: x.replace('.txt', ''))

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
    if config['version'] == 'expanded_trimmed':
        topic_data = pd.read_csv(config['input_path'] + 'LDA_01_topics.txt', sep = '\t', header = None)
        topic_keys = pd.read_csv(config['input_path'] + 'LDA_01_keys.txt', sep = '\t', header=None)
    elif config['version'] == 'coherence':
        topic_data = pd.read_csv(config['input_path'] + '40_Coherence_topics.txt', sep = '\t', header = None)
        topic_keys = pd.read_csv(config['input_path'] + '40_Coherence_keys.txt', sep = '\t', header=None)
    elif config['version'] == 'pre_1800':
        topic_data = pd.read_csv(config['input_path'] + 'Pre-Post-1800.txt', sep = '\t', header = None)        
        topic_keys = pd.read_csv(config['input_path'] + 'Pre-Post-1800_keys.txt', sep = '\t', header=None)
    else:
        raise ValueError("Invalid version specified. Please choose 'expanded_trimmed', 'coherence', or 'pre_1800'.")
    

    metadata = pd.read_csv(config['input_path'] + 'metadata_march25.csv')
    sentiment = pd.read_csv(config['input_path'] + 'sentiment_results_march25.csv')
    updated_progress = pd.read_csv(config['input_path'] + 'updated_progress_scores_march25.csv')
    industry = pd.read_csv(config['input_path'] + 'industry_scores_jan2025.csv')
    industry_scores_full_dict = pd.read_csv(config['input_path'] + 'industry_scores_full_dict.csv')
    updated_optimism_industry = pd.read_csv(config['input_path'] + 'industry_optimism_may_2025.csv')
    progress_chatgpt = pd.read_csv(config['input_path'] + 'progress_chatgpt_v2.csv')


    print('Volume Data Dimensions:' + str(topic_data.shape))
    topic_data_cleaned = clean_htids_topic_numbers(data = topic_data, string_identifier='/Cleaned_Nov2024/')
    print('Volume Data Cleaned Dimensions:' + str(topic_data_cleaned.shape))

    #fix topic numbers
    topic_keys.drop(columns=0, inplace=True)
    topic_keys['topic_number'] = list(range(1,len(topic_keys)+1))
    topic_keys.columns = ['weight', 'words', 'topic_number']

    metadata = metadata.rename(columns={'Unnamed: 0': 'HTID', 'year': 'Year'})
    metadata['Year_rounded'] = pd.to_numeric(metadata['Year'])
    metadata['Year'] = pd.to_numeric(metadata['Year'], downcast='signed')
    metadata['HTID'] = metadata.apply(fix_htid, axis=1)
    translations = pd.read_csv(config['input_path'] + 'translations.csv')
    translations['HTID'] = translations.apply(fix_htid, axis=1)
    metadata = metadata.merge(translations, on= 'HTID', how = 'left')

    #flag manual and related words
    metadata = flag_words(df = metadata, colnames=['title_translations', 'description'], words=manual_and_related_words, new_colname='manual_flag')
    metadata = metadata.drop(columns=['title_translations', 'description'], axis=1)

    sentiment = sentiment.rename(columns = {'Unnamed: 0': 'HTID', 'Regression': 'percent_regression', 'Pessimism': 'percent_pessimism', 'Optimism':'percent_optimistic', 'Progress': 'percent_progress_original'})
    sentiment['HTID'] = sentiment['HTID'].map(lambda x: x.replace('.txt', '')) #remove '.txt' at the end of each string for HTIDs

    updated_progress = updated_progress.rename(columns={'Unnamed: 0': 'HTID', 'Main': 'percent_progress_main', 'Progress': 'percent_progress_secondary'})
    updated_progress['HTID'] = updated_progress['HTID'].map(lambda x: x.replace('.txt', ''))

    industry = industry.rename(columns={'Unnamed: 0': 'HTID', 'Industrial Scores (June 23)':'industry'})
    industry['HTID'] = industry['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs

    industry_scores_full_dict = industry_scores_full_dict.rename(columns={'Unnamed: 0': 'HTID', 'Industrial Scores (All words)':'industry_full_dict'})
    industry_scores_full_dict['HTID'] = industry_scores_full_dict['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs

    updated_optimism_industry = updated_optimism_industry.rename(columns={'Unnamed: 0': 'HTID', 'Optimism Double Meaning':'optimism_abbreviated', 'Industrialization Prior': 'industry_1708'})
    updated_optimism_industry['HTID'] = updated_optimism_industry['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs

    progress_chatgpt = progress_chatgpt.rename(columns={'Unnamed: 0': 'HTID', 'ChatGPT Progress': 'progress_chatgpt'})
    progress_chatgpt['HTID'] = progress_chatgpt['HTID'].map(lambda x: x.replace('.txt', ''))#remove '.txt' at the end of each string for HTIDs

    sentiment_dfs = [industry, industry_scores_full_dict, sentiment, updated_progress, updated_optimism_industry, progress_chatgpt]

    print('Sentiment Dimensions:' + str(sentiment.shape))
    print('Industry Dimensions:' + str(industry.shape))
    print('Updated Progress Dimensions:' + str(updated_progress.shape))

    sentiment_scores_all = reduce(lambda left,right: pd.merge(left, right, on = 'HTID', how = 'inner'), sentiment_dfs) #merge on volume ID

    sentiment_scores_all.fillna(0, inplace=True) #fill NA values with 0, for a few novels without words.

    print('Merged Dimensions:' + str(sentiment_scores_all.shape))

    print('Exporting Data')
    topic_data_cleaned.to_csv(config['temporary_path'] + 'topic_weights.csv', index = False)
    topic_keys.to_csv(config['temporary_path'] + 'topics.csv', index = False)
    metadata.to_csv(config['temporary_path'] + 'metadata.csv', index=False)
    sentiment_scores_all.to_csv(config['temporary_path'] + 'sentiment_scores.csv', index=False)

    del topic_data, topic_keys, metadata, topic_data_cleaned, sentiment, updated_progress, industry, sentiment_scores_all, industry_scores_full_dict, updated_optimism_industry, progress_chatgpt
    gc.collect()

def run_clean_data(config):

    #make directories if they don't exist
    make_dir(config['temporary_path'])
    make_dir(config['output_path'])


    if config['version'] == 'baseline':
        run_clean_data_baseline(config)
    else:
        run_clean_data_expanded_trimmed(config)