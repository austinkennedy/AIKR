import pandas as pd
import gc


def moving_shares(data, year, bins=True):
    #get 20-year moving average of data, if bins = True
    if bins:
        df = data[(data['Year'] >= (year-10)) & (data['Year'] <= (year+10))] #grab volumes within +/- 10 year window
    else:
        df = data[data['Year'] == year]


    df.drop(columns = 'Year', inplace=True)

    if 'HTID' in df.columns:
        df.drop(columns = ['HTID'], inplace=True)
    
    share = df.sum(axis=0) / sum(df.sum(axis=0)) #numerator gets sum of each cross-topic across all volumes, denominator gets sum of all cross-topics over all volumes in window

    return share

def run_shares(config):
    print('Calculating Moving Average Shares')
    print('Importing Data')
    cross = pd.read_parquet(config['temporary_path'] + 'cross_topics.parquet')
    metadata = pd.read_csv(config['temporary_path'] + 'metadata.csv')
    cross = pd.merge(cross, metadata[['HTID', 'Year']], on='HTID', how='inner')
    
    #create sequence of years
    years=[]
    for year in range(1510,1891):
        years.append(year)

    ct_shares = {}
    for year in years:
        ct_shares[year] = moving_shares(cross, year, bins = config['bins'])

    moving_average_shares = pd.DataFrame.from_dict(ct_shares)
    print(moving_average_shares.head())
    print('Exporting data')
    moving_average_shares.to_csv(config['temporary_path'] + 'moving_average_shares.csv', index=True)

    del cross, metadata, ct_shares, moving_average_shares
    gc.collect()


