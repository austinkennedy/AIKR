import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px
import os
import statistics
from src.utils import  make_dir
plt.style.use('seaborn-white')

def category_averages(data, year, category):
    #get category averages within a category

    cat_vols = data[data['Category'] == category]
    cols = cat_vols[['Religion', 'Science', 'Political Economy']]
    means = np.array(cols.mean(axis = 0))
    means = means[None,:]
    tmp = pd.DataFrame(means, columns=cols.columns)
    tmp['Year'] = year
    # tmp['Volumes'] = len(cat_vols)
    return tmp

def category_averages_overall(data):
    #get overall category averages
    cols = data[['Religion', 'Science', 'Political Economy']]
    means = np.array(cols.mean(axis = 0))
    means = means[None,:]
    tmp = pd.DataFrame(means, columns=cols.columns)
    tmp['Year'] = year
    return tmp

def ternary_plots(data, color, filepath, legend_title, years, grayscale = False, size = None, decreasing_scale = False, show_legend = True):
    #'data' needs to be a dictionary of dataframes, with volumes as rows, and columns 'Religion', 'Political Economy', and 'Science'
    #'color': which variable color of dots will be based on
    #'path': directory to save output figures
    #'years': a list of years you want figures for
    #'grayscale': True if you want grayscale, will reverse color scale as well
    #'size': variable that determines size of dots, None by default
    #'increasing_scale': If 'True', size of dots will be bigger with bigger values of the 'size' variable

    s = str(size)

    for year in years:
        df = data[year]
        print(year)

        if decreasing_scale is True:
            df['size_percentile_r'] = 1 - df['industry_3_percentile']
            size = 'size_percentile_r'


        fig = px.scatter_ternary(df, a = 'Religion', b = 'Political Economy', c = 'Science',
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

        #check if directory in path exists, if not create it
        make_dir(path = filepath)

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

    #create sequence of years
    years=[]
    for year in range(1510,1891):
        years.append(year)

    moving_volumes = {}

    for year in years:
        if config['bins']:
            df = volumes[(volumes['Year'] >= (year-10)) & (volumes['Year'] <= (year+10))] #grab volumes within +/- 10 year window
        else:
            df = volumes[volumes['Year'] == year]

        moving_volumes[year] = df

    half_centuries = []
    for year in range(1550,1891,50):
        half_centuries.append(year)

    for fig in config['ternary_figs']:
        ternary_plots(data=moving_volumes,
                      years = half_centuries,
                      color=fig['color'],
                      filepath=config['output_path'] + fig['filepath'],
                      grayscale=fig['grayscale'],
                      size=fig['size'],
                      decreasing_scale=fig['decreasing_scale'],
                      legend_title=fig['legend_title'],
                      show_legend=fig['show_legend']
                      )


