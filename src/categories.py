
import pandas as pd
import itertools
import gc
from math import comb

#functions
def cross_share(data):
    df = data.copy() #Won't modify original object

    if 'HTID' in df.columns:
        df.drop(columns = ['HTID'], inplace=True)
    
    share = df.sum(axis = 0) / sum(df.sum(axis=0)) #numerator: sum down across rows, denominator: sum the sum of rows to get total of all cross-topics
    return share


def get_shares(shares, top, omit = None, length = 3):
    #'topics' is a list or dataframe of topics, where each row corresponds to a topic
    #'omit' is a list of topics to omit, should be a list of numbers
    #'length' is the size of the categories (i.e. how many topics should make up a category), default 3

    n = len(top) #get number of topics
    topic_numbers = list(top['topic_number']) # generate topic numbers
    topic_dict = pd.Series(top['words'].values, index = top.topic_number).to_dict() #mapping of topic numbers and words

    if omit is not None:
        topic_numbers = [i for i in topic_numbers if i not in omit] #remove innocuous topics
    
    topic_numbers.sort() #itertools.combinations needs sorted list
    combos = list(itertools.combinations(topic_numbers, r = length)) #create combinations of desired length

    combo_sets = [set(i) for i in combos] #get set of topic numbers for each row, i is each combo, contained in a tuple

    cross_combos = [list(itertools.combinations(i,2)) for i in combos]#gets every combination of elements in row from combos, i.e. for (1,2,3) gets (1,2),(1,3),(2,3)
    cross_combos = [['x'.join(map(str, i)) for i in c] for c in cross_combos] #joins each topic pair with 'x' to reference 'shares'
    cross_shares = [[shares[str(i)] for i in c] for c in cross_combos] #get share for each element
    cross_sum = [sum(i) for i in cross_shares] #sum each row
    topic_words = [[topic_dict[i] for i in t] for t in combos]

    #column names
    topic_names = ['topic' + str(i) for i in range(1, length+1)]
    cross_names = ['combination' + str(i) for i in range(1, comb(length, 2)+1)] #'math.comb' gives the number of combinations, not the combinations themselves
    share_names = ['share' + str(i) for i in range(1, comb(length, 2)+1)]
    topic_words_names = ['words' + str(i) for i in range(1, length+1)]

    #convert to dataframes since each are lists of tuples, easier to join
    combos = pd.DataFrame(combos, columns=topic_names)
    combo_sets = pd.DataFrame(pd.Series(combo_sets), columns=['Sets'])
    cross_combos = pd.DataFrame(cross_combos, columns=cross_names)
    cross_shares = pd.DataFrame(cross_shares, columns=share_names)
    cross_sum = pd.DataFrame(cross_sum, columns=['Sum'])
    topic_words = pd.DataFrame(topic_words, columns=topic_words_names)


    tmp = pd.concat([combos, combo_sets, cross_combos, cross_shares, cross_sum, topic_words], axis = 1)
    df = pd.DataFrame(tmp)
    # df = pd.DataFrame(tmp, columns=[topic_names, cross_names, share_names, 'Sum'])
    df.sort_values('Sum', ascending = False, inplace = True)

    return df

def distinct_categories(data):
    #algorithm to get distinct categories
    #takes the output of 'get_shares' function and finds unique categories
    #'Sets' in 'data' is a column with the set of topics in each row

    data.sort_values('Sum', ascending = False, inplace = True) #Make sure values are sorted

    seen = set([]) #create empty set
    unique = [] #list for appending unique rows

    for ind, row in data.iterrows():
        if bool(row['Sets'] & seen): #checks if any elements in 'Set' are in 'seen', if so, move to next row
            pass
        else:
            unique.append(row) #if the set is unique, grab row
            seen.update(row['Sets']) #add set of topics to 'seen'

    df = pd.DataFrame(unique)

    return(df)

def run_categories(config):

    print('Loading Data')
    topics = pd.read_csv(config['temporary_path'] + 'topics.csv')
    cross = pd.read_parquet(config['temporary_path'] + 'cross_topics.parquet')

    print(len(cross))
    print(topics)

    print('Calculating shares')
    shares_all = cross_share(cross)
    print(shares_all)

    print('Getting categories')
    clusters = get_shares(shares = shares_all, top = topics, omit = config['eliminated_topics'], length = 3)

    print('Finding distinct categories')
    clusters_corpus = distinct_categories(clusters)
    print(clusters_corpus)

    print('Exporting Data')
    clusters.to_csv(config['temporary_path'] + 'clusters.csv', index = False)
    shares_all.to_csv(config['temporary_path'] + 'shares.csv', index = True)

    del topics, cross, shares_all, clusters, clusters_corpus
    gc.collect()

