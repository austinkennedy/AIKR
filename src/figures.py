import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px
import os
import gc
import statistics
from src.utils import  make_dir
plt.style.use('seaborn-white')

def category_averages_by_year(data, year, category, categories):
    #get category averages within a category

    cat_vols = data[data['Category'] == category]
    cols = cat_vols[categories]
    means = np.array(cols.mean(axis = 0))
    means = means[None,:]
    tmp = pd.DataFrame(means, columns=cols.columns)
    tmp['Year'] = year
    # tmp['Volumes'] = len(cat_vols)
    return tmp

def category_averages_overall(data, year, categories):
    #get overall category averages
    cols = data[categories]
    means = np.array(cols.mean(axis = 0))
    means = means[None,:]
    tmp = pd.DataFrame(means, columns=cols.columns)
    tmp['Year'] = year
    return tmp

def calculate_summary_data(volumes, years, categories, config):

    category_counts_by_year = volumes.groupby(['Year', 'Category'])['HTID'].count().unstack(fill_value=0).reset_index() #get counts of each category by year

    
    volumes_time = {cat: [] for cat in categories}
    cat_avgs = {}
    moving_volumes = {}
    avg_progress = {}

    for year in years:
        
        if config['bins']:
            df = volumes[(volumes['Year'] >= (year-10)) & (volumes['Year'] <= (year+10))]
        else:
            df = volumes[volumes['Year'] == year]

        for category in categories:
            volumes_time[category].append(category_averages_by_year(df, year, category, categories))

        cat_avgs[year] = category_averages_overall(df, year, categories)
        moving_volumes[year] = df.copy()

        if len(volumes[volumes['Year'] == year]) != 0:
            avg_progress[year] = statistics.mean(volumes[volumes['Year'] == year]['progress_main_percentile'])
        else:
            avg_progress[year] = np.nan



    #do a little data cleaning
    for category in categories:
        volumes_time[category] = pd.concat(volumes_time[category], ignore_index=True)
        counts = category_counts_by_year[['Year', category]].rename(columns={category: 'Volumes'}) #get volume count for each category by year
        volumes_time[category] = pd.merge(volumes_time[category], counts, on='Year', how = 'left') #merge counts with category averages, by category
        volumes_time[category]['Volumes_rolling'] = volumes_time[category]['Volumes'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    cat_avgs = pd.concat(cat_avgs).reset_index(drop=True)

    avg_progress = pd.DataFrame.from_dict(avg_progress, orient='index').reset_index()
    avg_progress.columns = ['Year', 'avg_progress']

    return moving_volumes, cat_avgs, volumes_time, avg_progress


def category_plots(volumes_time, categories, config, ymax):

    for category in categories:
        df = volumes_time[category]
        fig, (ax1) = plt.subplots(1,1)
        colors = ['b', 'g', 'r']
        lines = ['dashdot', 'dashed', 'dotted']
        for i, cat in enumerate(categories):
            ax1.plot(df['Year'], df[cat], label = cat, color = colors[i], linestyle = lines[i])
        
        ax1.legend(loc = 'upper right')
        plt.ylim([0,0.8])
        ax1.title.set_text(category + ' Volumes')

        ax2 = ax1.twinx()
        ax2.set_ylabel('# of volumes')
        ax2.plot(df['Year'], df['Volumes_rolling'], color = 'black', linestyle = 'solid', label = 'Total Volumes')
        ax2.legend(loc = 'upper center')
        ax2.set_ylim([0, ymax])

        fig.savefig(config['output_path'] + 'volumes_over_time/' + category + '.png', dpi = 200)


def volume_count_plots(volume_counts_by_year, config):

    df = volume_counts_by_year.copy()
    df['Count_rolling'] = df['Count'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    #raw values plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['Count'], label = 'Volume Count', color = 'darkblue', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'total_volumes_raw.png', dpi = 200)

    #rolling average plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['Count_rolling'], label = 'Volume Count', color = 'darkblue', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'total_volumes.png', dpi = 200)

def progress_plots(avg_progress, config):
    df = avg_progress.copy()
    df['avg_progress_rolling'] = df['avg_progress'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    #raw values plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_progress'], label = 'Average Progress Score (Percentile)', color = 'crimson', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_raw.png', dpi = 200)

    #rolling average plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_progress_rolling'], label = 'Average Progress Score (Percentile)', color = 'crimson', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress.png', dpi = 200)

def topic_ternary_plots(config, topic_shares, years, categories):

    make_dir(config['output_path'] + 'topic_triangles/')

    #create and export ternary plots
    for year in years:
        fig = px.scatter_ternary(topic_shares[year],
                                    a = categories[0], b = categories[1], c = categories[2],
                                    color = 'Color',
                                    color_discrete_map = {categories[0]: 'blue', categories[1]:'red', categories[2]: 'green'},
                                    template = 'simple_white',
                                    symbol = "Color",
                                    symbol_map = {categories[0]: 'cross', categories[1]: 'triangle-up', categories[2]: 'circle'})

        fig.update_traces(showlegend=False, marker = {'size': 10})
        fig.update_layout(title_text = str(year), title_font_size=30, font_size=20)

        if year == 1850:
            #add legend and adjust size for 1850
            fig.update_traces(showlegend=True)
            fig.update_layout(legend = dict(y=0.5), legend_title_text = 'Legend')
            fig.write_image(config['output_path'] + 'topic_triangles/' + str(year) +'.png', width = 900)
        else:
            fig.write_image(config['output_path'] + 'topic_triangles/' + str(year) +'.png')
        



def ternary_plots(data, color, filepath, legend_title, years, categories, grayscale = False, size = None, decreasing_scale = False, show_legend = True):
    #'data' needs to be a dictionary of dataframes, with volumes as rows, and columns 'Religion', 'Political Economy', and 'Science'
    #'color': which variable color of dots will be based on
    #'path': directory to save output figures
    #'years': a list of years you want figures for
    #'grayscale': True if you want grayscale, will reverse color scale as well
    #'size': variable that determines size of dots, None by default
    #'increasing_scale': If 'True', size of dots will be bigger with bigger values of the 'size' variable

    print(legend_title)

    s = str(size)

    make_dir(path = filepath)

    for year in years:
        df = data[year]
        print(year)

        if decreasing_scale is True:
            df['size_percentile_r'] = 1 - df[s]
            size = 'size_percentile_r'


        fig = px.scatter_ternary(df, a = categories[0], b = categories[1], c = categories[2],
                                 color = color,
                                 size = size,
                                 size_max=13,
                                 range_color=[0,1])
        
        fig.update_layout(title_text = str(year),
                        title_font_size=30,
                        font_size=20,
                        margin_l = 110,
                        legend_title_side = 'top',
                        coloraxis_colorbar_title_text = 'Percentile',
                        coloraxis_colorbar_title_side = 'top'
                        )
        
        fig.update_ternaries(bgcolor="white",
                        aaxis_linecolor="black",
                        baxis_linecolor="black",
                        caxis_linecolor="black"
                        )
        
        if grayscale is True:
            fig.update_layout(coloraxis = {'colorscale':'gray'})

        fig.update_traces(
            showlegend = False
        )

        if year == 1850 and show_legend is True:   
            fig.write_image(filepath + str(year) + '.png', width=900) #included because wider format needed for color scale
        
        else:
            fig.update(layout_coloraxis_showscale=False) #removes colorbar
            fig.write_image(filepath + str(year) + '.png') #only works with kaleido 0.1.0 for some reason, use 'conda install python-kaleido=0.1.0post1' on PC, also uses plotly 5.10.0
        
        # Uncomment for no legend at all
        # fig.update(layout_coloraxis_showscale=False) #removes colorbar
        # fig.write_image(path + str(year) + '.png') #only works with kaleido 0.1.0 for some reason, use 'conda install python-kaleido=0.1.0post1' on PC, also uses plotly 5.10.0


def run_figures(config):
    print('Creating Figures')
    print('Importing Data')
    volumes = pd.read_csv(config['temporary_path'] + 'volumes_scores.csv')
    #load pickle file
    topic_shares = pd.read_pickle(config['temporary_path'] + 'topic_shares.pickle')

    #create sequence of all years
    all_years = []
    for year in range(1500,1900):
        all_years.append(year)

    #create sequence of years
    years=[]
    for year in range(1510,1891):
        years.append(year)

    half_centuries = []
    for year in range(1550,1891,50):
        half_centuries.append(year)

    categories = list(config['categories'].keys()) #extracts category names from config
    volumes['Category'] = volumes[categories].idxmax(axis=1) #get category of each volume

    #find category for each topic, based on shares in 1850
    for year in years:
        topic_shares[year]['Color'] = topic_shares[1850][categories].idxmax(axis=1)

    #count overall volumes by year
    volume_counts_by_year = volumes.groupby('Year')['HTID'].count().reset_index()#get counts of each category by year
    #fill missing years with 0
    volume_counts_by_year = volume_counts_by_year.set_index('Year').reindex(all_years, fill_value=0).reset_index().rename(columns={'HTID': 'Count'})

    moving_volumes, cat_avgs, volumes_time, avg_progress = calculate_summary_data(volumes, years, categories, config)

    make_dir(config['output_path'] + 'volumes_over_time/')

    category_plots(volumes_time, categories, config, config['category_plots_ymax'])

    topic_ternary_plots(config, topic_shares, half_centuries, categories)

    volume_count_plots(volume_counts_by_year, config)

    progress_plots(avg_progress, config)

    for fig in config['ternary_figs']:
        ternary_plots(data=moving_volumes,
                      years = half_centuries,
                      categories=categories,
                      color=fig['color'],
                      filepath=config['output_path'] + fig['filepath'],
                      grayscale=fig['grayscale'],
                      size=fig['size'],
                      decreasing_scale=fig['decreasing_scale'],
                      legend_title=fig['legend_title'],
                      show_legend=fig['show_legend']
                      )
        
    del volumes, moving_volumes, cat_avgs, volumes_time, avg_progress, volume_counts_by_year
    gc.collect()


