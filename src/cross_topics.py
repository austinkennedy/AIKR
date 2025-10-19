import pandas as pd
import numpy as np
import gc

#Function for getting cross-topic weights
def cross_multiply(df):
    #multiplies every column by every other column. Pass a dataframe with volumes as rows and topic weights as columns. 'HTID' column not required, but preferred

        
    i = 0
    ls = []

    if 'HTID' in df.columns:
        #handles data with a column for 'HTID'
        htids = df['HTID']
        df = df.drop(columns = 'HTID')
        ls.append(pd.DataFrame(htids, columns=['HTID']))

    names = df.columns.tolist() #get column names

    while i < len(df.columns):
        a = np.array(df.iloc[:,i])

        b = np.array(df.iloc[:,i+1:])


        c = (b.T * a).T #element-wise multiplication, multiplies topic weight by every other weight for each volume

        cols = [str(names[i]) + 'x' + str(j) for j in names[i+1:]] #column names, 'topic1 x topic2'
        
        ls.append(pd.DataFrame(c, columns=cols))

        if i == 0:
            print(pd.DataFrame(a))
            print(pd.DataFrame(b))
            print(pd.DataFrame(c))
            print(ls)

        i += 1

    cr = pd.concat(ls, axis = 1) #append across columns



    return cr

def run_cross_topics(config):
    print('Running cross-topic weights')
    print('Importing Data')
    data = pd.read_csv(config['temporary_path'] + 'topic_weights.csv')
    print('Calculating cross-topic weights')
    cross = cross_multiply(data)
    print(cross)
    print('Exporting Data')
    cross.to_parquet(config['temporary_path'] + 'cross_topics.parquet', index = False)
    cross.to_csv(config['temporary_path'] + 'cross_topics.csv', index = False)

    del data, cross
    gc.collect()