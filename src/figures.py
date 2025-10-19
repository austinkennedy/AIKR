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
    cat_avgs_transl = {}
    cat_avgs_manual = {}
    moving_volumes = {}
    avg_progress = {}
    avg_progress_transl = {}
    avg_progress_manual = {}
    avg_industry = {}

    for year in years:
        
        if config['bins']:
            df = volumes[(volumes['Year'] >= (year-10)) & (volumes['Year'] <= (year+10))]
        else:
            df = volumes[volumes['Year'] == year]

        df_transl = df[df['translation'] == 1] #get only translated volumes
        df_manual = df[df['manual_flag'] == 1] #get only volumes that reference manual or related words

        for category in categories:
            volumes_time[category].append(category_averages_by_year(df, year, category, categories))

        cat_avgs[year] = category_averages_overall(df, year, categories)
        cat_avgs_transl[year] = category_averages_overall(df_transl, year, categories)
        cat_avgs_manual[year] = category_averages_overall(df_manual, year, categories)
        moving_volumes[year] = df.copy()

        if len(volumes[volumes['Year'] == year]) != 0:
            avg_progress[year] = statistics.mean(volumes[volumes['Year'] == year]['progress_main_percentile'])
        else:
            avg_progress[year] = np.nan

        if len(df_transl) > 0:
            avg_progress_transl[year] = statistics.mean(df_transl['progress_main_percentile'])
        else:
            avg_progress_transl[year] = np.nan

        if len(df_manual) > 0:
            avg_progress_manual[year] = statistics.mean(df_manual['progress_main_percentile'])
        else:
            avg_progress_manual[year] = np.nan

        if len(volumes[volumes['Year'] == year]) != 0:
            avg_industry[year] = statistics.mean(volumes[volumes['Year'] == year]['industry_percentile'])
        else:
            avg_industry[year] = np.nan



    #do a little data cleaning
    for category in categories:
        if category not in category_counts_by_year.columns:
            category_counts_by_year[category] = 0
            
        volumes_time[category] = pd.concat(volumes_time[category], ignore_index=True)
        counts = category_counts_by_year[['Year', category]].rename(columns={category: 'Volumes'}) #get volume count for each category by year
        volumes_time[category] = pd.merge(volumes_time[category], counts, on='Year', how = 'left') #merge counts with category averages, by category
        volumes_time[category]['Volumes_rolling'] = volumes_time[category]['Volumes'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    cat_avgs = pd.concat(cat_avgs).reset_index(drop=True)
    cat_avgs_transl = pd.concat(cat_avgs_transl).reset_index(drop=True)
    cat_avgs_manual = pd.concat(cat_avgs_manual).reset_index(drop=True)

    avg_progress = pd.DataFrame.from_dict(avg_progress, orient='index').reset_index()
    avg_progress.columns = ['Year', 'avg_progress']

    avg_progress_transl = pd.DataFrame.from_dict(avg_progress_transl, orient='index').reset_index()
    avg_progress_transl.columns = ['Year', 'avg_progress']

    avg_progress_manual = pd.DataFrame.from_dict(avg_progress_manual, orient='index').reset_index()
    avg_progress_manual.columns = ['Year', 'avg_progress']

    avg_industry = pd.DataFrame.from_dict(avg_industry, orient='index').reset_index()
    avg_industry.columns = ['Year', 'avg_industry']

    return moving_volumes, cat_avgs, cat_avgs_transl, cat_avgs_manual, volumes_time, avg_progress, avg_progress_transl, avg_progress_manual, avg_industry


def category_plots(volumes_time, categories, config, ymax):

    for category in categories:
        df = volumes_time[category]
        fig, (ax1) = plt.subplots(1,1)
        colors = ['b', 'r', 'g']
        lines = ['dashdot', 'dotted', 'dashed']
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

def category_averages_translations(cat_avgs, cat_avgs_transl, config, categories):
    
    fig, (ax1) = plt.subplots(1,1, figsize=(9,6))
    colors = ['b', 'r', 'g']
    lines_non_transl = ['solid', 'dotted', 'dashdot']
    lines_transl = ['dashed', (0, (1,1)), (0, (3,5,1,5))]

    for i, cat in enumerate(categories):
        ax1.plot(cat_avgs['Year'], cat_avgs[cat], label = cat, color = colors[i], linestyle = lines_non_transl[i])
        ax1.plot(cat_avgs_transl['Year'], cat_avgs_transl[cat], label = cat + ' (Translations)', color = colors[i], linestyle = lines_transl[i])
    plt.legend(loc= 'upper center', ncol = 3)
    plt.ylim([0,1])

    fig.savefig(config['output_path'] + 'volumes_over_time/corpus_vs_transl_categories.png', dpi=200)

def category_averages_manual(cat_avgs, cat_avgs_manual, config, categories):
    fig, (ax1) = plt.subplots(1,1, figsize=(9,6))
    colors = ['b', 'r', 'g']
    lines_non_transl = ['solid', 'dotted', 'dashdot']
    lines_manual = ['dashed', (0, (1,1)), (0, (3,5,1,5))]

    for i, cat in enumerate(categories):
        ax1.plot(cat_avgs['Year'], cat_avgs[cat], label = cat, color = colors[i], linestyle = lines_non_transl[i])
        ax1.plot(cat_avgs_manual['Year'], cat_avgs_manual[cat], label = cat + ' (Manuals)', color = colors[i], linestyle = lines_manual[i])
    plt.legend(loc= 'upper center', ncol = 3)
    plt.ylim([0,1])

    fig.savefig(config['output_path'] + 'volumes_over_time/corpus_vs_manual_categories.png', dpi=200)


def volume_count_plots(volume_counts_by_year, config):

    df = volume_counts_by_year.copy()
    df['Count_rolling'] = df['Count'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    #raw values plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['Count'], label = 'Volume Count', color = 'darkblue', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    #move legend to the upper left corner
    ax1.legend(loc = 'upper left')
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'total_volumes_raw.png', dpi = 200)

    #rolling average plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['Count_rolling'], label = 'Volume Count', color = 'darkblue', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.legend(loc = 'upper left')
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'total_volumes.png', dpi = 200)

def progress_plots(avg_progress, config, translations = False, manual = False, avg_progress_transl = None, avg_progress_manual = None):
    df = avg_progress.copy()
    df['avg_progress_rolling'] = df['avg_progress'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    if translations and manual:
        return ValueError('Please choose either translations or manual, not both.')

    if avg_progress_transl is not None:
        df_transl = avg_progress_transl.copy()
        df_transl['avg_progress_rolling'] = df_transl['avg_progress'].rolling(window=20, min_periods=1, center = True).mean()

    if avg_progress_manual is not None:
        df_manual = avg_progress_manual.copy()
        df_manual['avg_progress_rolling'] = df_manual['avg_progress'].rolling(window=20, min_periods=1, center = True).mean()

    #raw values plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_progress'], label = 'Average Progress Score (Percentile)', color = 'crimson', linestyle = 'solid')
    if translations:
        ax1.plot(df['Year'], avg_progress_transl['avg_progress'], label = 'Average Progress Score (Translations)', color = 'crimson', linestyle = 'dashed')
    elif manual:
        ax1.plot(df['Year'], df_manual['avg_progress'], label = 'Average Progress Score (Manuals)', color = 'crimson', linestyle = 'dashed')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    if translations:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_translations_raw.png', dpi = 200)
    elif manual:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_manual_raw.png', dpi = 200)
    else:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_raw.png', dpi = 200)

    #rolling average plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_progress_rolling'], label = 'Average Progress Score (Percentile)', color = 'crimson', linestyle = 'solid')
    if translations:
        ax1.plot(df['Year'], df_transl['avg_progress_rolling'], label = 'Average Progress Score (Translations)', color = 'crimson', linestyle = 'dashed')
    elif manual:
        ax1.plot(df['Year'], df_manual['avg_progress_rolling'], label = 'Average Progress Score (Manuals)', color = 'crimson', linestyle = 'dashed')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    if translations:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_translations.png', dpi = 200)
    elif manual:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress_manual.png', dpi = 200)
    else:
        fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_progress.png', dpi = 200)

def industry_plots(avg_industry, config):
    df = avg_industry.copy()
    df['avg_industry_rolling'] = df['avg_industry'].rolling(window=20, min_periods=1, center = True).mean() #rolling average of volumes

    #raw values plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_industry'], label = 'Average Industry Score (Percentile)', color = 'crimson', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_industry_raw.png', dpi = 200)

    #rolling average plot
    fig, (ax1) = plt.subplots(1,1)
    ax1.plot(df['Year'], df['avg_industry_rolling'], label = 'Average Industry Score (Percentile)', color = 'crimson', linestyle = 'solid')
    ax1.legend(loc = 'upper right')
    ax1.set_xlabel('Year')
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1])
    fig.savefig(config['output_path'] + 'volumes_over_time/' + 'avg_industry.png', dpi = 200)

def topic_ternary_plots(config, topic_shares, years, categories):

    make_dir(config['output_path'] + 'topic_triangles/color/')
    make_dir(config['output_path'] + 'topic_triangles/grayscale/')

    gray_map = {
        categories[0]: 'rgb(120, 120, 120)',
        categories[1]: 'rgb(180, 180, 180)',
        categories[2]: 'rgb(60, 60, 60)'
    }

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
            fig.update_traces(showlegend=True)
            fig.update_layout(legend = dict(y=0.5), legend_title_text = 'Legend')

        fig.write_image(config['output_path'] + 'topic_triangles/color/' + str(year) +'.png', width = 900)

        for trace in fig.data:
            cat = trace.name
            if cat in gray_map:
                trace.marker.color = gray_map[cat]

        fig.write_image(config['output_path'] + 'topic_triangles/grayscale/' + str(year) +'.png', width = 900)


def estc_distribution_plot(config, estc_data, volume_counts_by_year, all_years):
        """Create ESTC vs. HDL volume distribution plots"""
        
        make_dir(config['output_path'] + 'estc_figures/')

        estc_data['Year'] = estc_data['Publisher/year'].str.replace(r"\D", '')
        estc_data['Year'] = estc_data['Year'].replace('', np.nan)
        estc_data = estc_data.dropna(subset = ['Year'])
        estc_data['Year'] = estc_data['Year'].astype('float64')
        estc_data = estc_data[(estc_data['Year'] >= 1500) & (estc_data['Year'] <= 1800)]
        estc_data['Year'] = estc_data['Year'].astype('int')
        estc_data.rename(columns = {'ESTC System No.': 'estc_id'}, inplace = True)

        estc_counts = estc_data.groupby('Year')['estc_id'].count().reset_index()
        estc_counts = estc_counts.set_index('Year').reindex(all_years, fill_value=0).reset_index().rename(columns={'estc_id': 'estc_volumes'})
        volume_counts = pd.merge(volume_counts_by_year, estc_counts, on = 'Year', how = 'left')
        volume_counts.rename(columns = {'Count': 'hathitrust_volumes'}, inplace = True)
        volume_counts = volume_counts[volume_counts['Year'] <= 1800]

        volume_counts['estc_volumes_rolling'] = volume_counts['estc_volumes'].rolling(window = 20, min_periods=1, center = True).mean()
        volume_counts['hathitrust_volumes_rolling'] = volume_counts['hathitrust_volumes'].rolling(window = 20, min_periods=1, center=True).mean()
        volume_counts['estc_cumulative'] = volume_counts['estc_volumes'].cumsum() / volume_counts['estc_volumes'].sum()
        volume_counts['hathitrust_cumulative'] = volume_counts['hathitrust_volumes'].cumsum() / volume_counts['hathitrust_volumes'].sum()
        volume_counts['estc_share'] = volume_counts['estc_volumes'] / volume_counts['estc_volumes'].sum()
        volume_counts['hathitrust_share'] = volume_counts['hathitrust_volumes'] / volume_counts['hathitrust_volumes'].sum()
        volume_counts['estc_rolling_share'] = volume_counts['estc_volumes_rolling'] / volume_counts['estc_volumes_rolling'].sum()
        volume_counts['hathitrust_rolling_share'] = volume_counts['hathitrust_volumes_rolling'] / volume_counts['hathitrust_volumes_rolling'].sum()

        fig, (ax1) = plt.subplots(1,1)
        ax1.plot(volume_counts['Year'], volume_counts['estc_cumulative'], color = 'red', label = 'ESTC')
        ax1.plot(volume_counts['Year'], volume_counts['hathitrust_cumulative'], color = 'darkblue', label = 'HDL')
        ax1.legend(loc = "upper left")
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Cumulative Share')
        ax1.set_yticks([0,0.25, 0.5, 0.75, 1])
        ax1.set_yticklabels(["0", "0.25", "0.5", "0.75", "1"])
        fig.savefig(config['output_path'] + 'estc_figures/estc_hathitrust_counts.png', dpi = 200)

        fig, (ax1) = plt.subplots(1,1)
        ax1.plot(volume_counts['Year'], volume_counts['estc_rolling_share'], color = 'red', label = 'ESTC', linestyle = 'dashed')
        ax1.plot(volume_counts['Year'], volume_counts['hathitrust_rolling_share'], color = 'darkblue', label = 'HDL')
        ax1.legend(loc = "upper left")
        ax1.set_xlabel('Year')
        ax1.set_ylabel('Share')
        ax1.set_yticks([0,0.01, 0.02, 0.03])
        ax1.set_yticklabels(["0", "0.01", "0.02", "0.03"])
        fig.savefig(config['output_path'] + 'estc_figures/estc_hathitrust_pdf.png', dpi = 200)



def ternary_plots(data, color, filepath, legend_title, years, categories, grayscale = False, size = None, decreasing_scale = False, show_legend = True, manual = False):
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

        if manual:
            df = df[df['manual_flag'] == 1]

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
                        caxis_linecolor="black",
                        # aaxis_min = 0.2,
                        # baxis_min = 0.35,
                        # caxis_min = 0.25,
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
    metadata = pd.read_csv(config['temporary_path'] + 'metadata.csv')
    #load pickle file
    topic_shares = pd.read_pickle(config['temporary_path'] + 'topic_shares.pickle')


    #create sequence of all years
    all_years = []
    for year in range(1500,1901):
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
    volume_counts_by_year = metadata.groupby('Year')['HTID'].count().reset_index()
    #fill missing years with 0
    volume_counts_by_year = volume_counts_by_year.set_index('Year').reindex(all_years, fill_value=0).reset_index().rename(columns={'HTID': 'Count'})

    moving_volumes, cat_avgs, cat_avgs_transl, cat_avgs_manual, volumes_time, avg_progress, avg_progress_transl, avg_progress_manual, avg_industry = calculate_summary_data(volumes, years, categories, config)

    make_dir(config['output_path'] + 'volumes_over_time/')

    category_plots(volumes_time, categories, config, config['category_plots_ymax'])
    category_averages_translations(cat_avgs, cat_avgs_transl, config, categories)
    category_averages_manual(cat_avgs, cat_avgs_manual, config, categories)

    topic_ternary_plots(config, topic_shares, half_centuries, categories)

    volume_count_plots(volume_counts_by_year, config)

    progress_plots(avg_progress, config)
    progress_plots(avg_progress, config, translations = True, avg_progress_transl = avg_progress_transl)
    progress_plots(avg_progress, config, manual = True, avg_progress_manual = avg_progress_manual)

    industry_plots(avg_industry, config)

    #Create ESTC vs. HDL volume distribution plots
    if config['version'] == 'expanded_trimmed':
        estc_data = pd.read_csv(config['input_path'] + 'estc_1500_to_1800.csv')
        estc_distribution_plot(config, estc_data, volume_counts_by_year, all_years)

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
                    show_legend=fig['show_legend'],
                    manual = fig.get('manual', False) #if manual is True, only include volumes that reference manual or related words
                    )
        
    
        
    del volumes, moving_volumes, cat_avgs, volumes_time, avg_progress, volume_counts_by_year
    gc.collect()


