#!/usr/bin/env python
# coding: utf-8

# ## Build a volatility skew application 
# 
# ### Description
# Build a grid-like Dash app with the dgrid_components.py module to display:
# 1. Volatility Skew of various Futures Options vs At-The-Money Volatility of those options
# 2. Volatility Skew of various Futures Options vs Price
# 3. At-The-Money Volatility of various Futures Options vs Price
# 
# ### Usage
# 1. Run all of the cells
# 2. The last cell that executes ```app.run_server``` will display a link to a local URL.  Click on the URL to see the application
# 

# In[ ]:


from IPython.display import display
import dash
import sys,os
if  not os.path.abspath('./') in sys.path:
    sys.path.append(os.path.abspath('./'))
if  not os.path.abspath('../') in sys.path:
    sys.path.append(os.path.abspath('../'))

import datetime
import pandas as pd
from scipy.signal import argrelextrema
import pandas_datareader as pdr
import numpy as np
import importlib
from scipy.stats import norm

from dashgrid import dgrid_components as dgc
import dash_html_components as html

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import plotly.graph_objs as go
import plotly.tools as tls
from plotly.offline import  init_notebook_mode, iplot
from plotly.graph_objs.layout import Font,Margin
init_notebook_mode(connected=True)
import pathlib
SYSTEM_HOME = pathlib.Path.home()
import tqdm
from tqdm import tqdm_notebook
import traceback


# ### Define a method that creates plotly line graphs

# In[ ]:


def plotly_plot(df_in,x_column,plot_title=None,
                y_left_label=None,y_right_label=None,
                bar_plot=False,figsize=(16,10),
                number_of_ticks_display=20,
                yaxis2_cols=None):
    ya2c = [] if yaxis2_cols is None else yaxis2_cols
    ycols = [c for c in df_in.columns.values if c != x_column]
    # create tdvals, which will have x axis labels
    td = list(df_in[x_column]) 
    nt = len(df_in)-1 if number_of_ticks_display > len(df_in) else number_of_ticks_display
    spacing = len(td)//nt
    tdvals = td[::spacing]
    
    # create data for graph
    data = []
    # iterate through all ycols to append to data that gets passed to go.Figure
    for ycol in ycols:
        if bar_plot:
            b = go.Bar(x=td,y=df_in[ycol],name=ycol,yaxis='y' if ycol not in ya2c else 'y2')
        else:
            b = go.Scatter(x=td,y=df_in[ycol],name=ycol,yaxis='y' if ycol not in ya2c else 'y2')
        data.append(b)

    # create a layout
    layout = go.Layout(
        title=plot_title,
        xaxis=dict(
            ticktext=tdvals,
            tickvals=tdvals,
            tickangle=45,
            type='category'),
        yaxis=dict(
            title='y main' if y_left_label is None else y_left_label
        ),
        yaxis2=dict(
            title='y alt' if y_right_label is None else y_right_label,
            overlaying='y',
            side='right'),
        margin=Margin(
            b=100
        )        
    )

    fig = go.Figure(data=data,layout=layout)
    return fig


# # Support methods for app below

# ### Create a logger

# In[ ]:


# a logger is always helpful
logger = dgc.init_root_logger('logfile.log','INFO') 


# ### Build main DataFrames that hold skew, atm vol and price info

# In[ ]:


DEFAULT_CONFIGS = {"PATH_DATA_HOME":"./",
                  "host":"127.0.0.1",
                  "port":8550,
                  "url_base_pathname":"futskew"}

# read configuration
import json
try:
    configs = json.load(open('./temp_folder/dgrid_components_futures_skew_example_app.json','r'))
    logger.info(f'using configs located at ./temp_folder/dgrid_components_futures_skew_example_app.json')
except:
    traceback.print_exc()
    logger.info(f'using default configs')
    configs = DEFAULT_CONFIGS.copy()

PATH_DATA_HOME = configs['PATH_DATA_HOME']#'../../barchartacs/barchartacs/temp_folder'
FILENAME_SKEW = 'df_iv_skew_COMMOD.csv'
FILENAME_IV = 'df_iv_final_COMMOD.csv'
FILENAME_FUT = 'df_cash_futures_COMMOD.csv'

df_iv_skew = None
df_iv_final = None
df_cash_futures = None
for commod in ['CL','CB','ES','NG']:
    fn_skew = FILENAME_SKEW.replace('COMMOD',commod)
    df_skew = pd.read_csv(f'{PATH_DATA_HOME}/{fn_skew}')
    fn_iv = FILENAME_IV.replace('COMMOD',commod)
    df_iv = pd.read_csv(f'{PATH_DATA_HOME}/{fn_iv}')
    fn_fut = FILENAME_FUT.replace('COMMOD',commod)
    df_fut = pd.read_csv(f'{PATH_DATA_HOME}/{fn_fut}')
    df_skew['commod'] = commod
    df_iv['commod'] = commod
    df_fut['commod'] = commod
    if df_iv_skew is None:
        df_iv_skew = df_skew.copy()
        df_iv_final = df_iv.copy()
        df_cash_futures = df_fut.copy()
    else:
        df_iv_skew = df_iv_skew.append(df_skew.copy())
        df_iv_final = df_iv_final.append(df_iv.copy())
        df_cash_futures = df_cash_futures.append(df_fut.copy())
df_iv_skew = df_iv_skew.rename(columns={c:float(c) for c in df_iv_skew.columns.values if '0.' in c})


# ## Define the components of the Dash App using the wrapper dgrid_components.py

# ### Create charts from DataFrames

# In[ ]:


def plot_skew_vs_atm(SYMBOL_TO_RESEARCH,df_iv_final_in,df_iv_skew_in,df_cash_futures_in,dist_from_zero=.1,year=None):
    # Step 00: select only SYMBOL_TO_RESEARCH from DataFrames 
    df_iv_final = df_iv_final_in[df_iv_final_in.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
    df_iv_skew = df_iv_skew_in[df_iv_skew_in.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
    df_cash_futures = df_cash_futures_in[df_cash_futures_in.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
    
    year = 'all' if year is None else year
    if str(year).lower() != 'all':
        y = int(str(year))
        beg_year = y*100*100+1*100+1
        end_year = y*100*100+12*100+31
        df_iv_final = df_iv_final[(df_iv_final.settle_date>=beg_year) & (df_iv_final.settle_date<=end_year)]
        df_iv_skew = df_iv_skew[(df_iv_skew.settle_date>=beg_year) & (df_iv_skew.settle_date<=end_year)]
        df_cash_futures = df_cash_futures[(df_cash_futures.settle_date>=beg_year) & (df_cash_futures.settle_date<=end_year)]

    # sort by settle_date
    df_iv_final = df_iv_final.sort_values('settle_date') 
    df_iv_skew = df_iv_skew.sort_values('settle_date') 
    df_cash_futures = df_cash_futures.sort_values('settle_date') 

    print(f'plot_skew_vs_atm year: {year}')

    # Step 01: create df_skew_2, which holds skew difference between 
    #   positive dist_from_zero and negative dist_from_zero, for each settle_date
    df_skew_2 = df_iv_skew.copy()
    df_skew_2.index.name = None
    skew_range_col = f'iv_skew'
    df_skew_2[skew_range_col] = df_skew_2[dist_from_zero] - df_skew_2[-dist_from_zero]
    df_skew_2.settle_date = df_skew_2.settle_date.astype(int)
    df_skew_2 = df_skew_2[['settle_date',skew_range_col]]
    
    # Step 02: create atm implied vol table, that also has the cash price for each settle_date
    df_atmv = df_iv_final[['settle_date','atm_iv']].drop_duplicates()
    df_cf = df_cash_futures[df_cash_futures.symbol==f'{SYMBOL_TO_RESEARCH}Z99']
    df_atmv = df_atmv.merge(df_cf[['settle_date','close']],how='inner',on='settle_date')
    
    # Step 03: merge skew and atm vol/close tables
    df_ivs = df_skew_2.merge(df_atmv,how='inner',on='settle_date')
    df_ivs = df_ivs.sort_values('settle_date')
    
    # Step 04: plot skew vs atm_iv
    chart_title = f'{SYMBOL_TO_RESEARCH} skew {dist_from_zero*100}% up and down vs atm vol'
    df_ivs_skew_vs_atm_iv = df_ivs[['settle_date',skew_range_col,'atm_iv']]
    fig_skew_vs_atm_iv = plotly_plot(df_ivs_skew_vs_atm_iv,x_column='settle_date',yaxis2_cols=['atm_iv'],
                      y_left_label='iv_skew',y_right_label='atm_iv',plot_title=chart_title)
    
    # Step 05: plot skew vs close
    chart_title = f'{SYMBOL_TO_RESEARCH} skew {dist_from_zero*100}% up and down vs close'
    df_ivs_skew_vs_close = df_ivs[['settle_date',skew_range_col,'close']]
    fig_skew_vs_close = plotly_plot(df_ivs_skew_vs_close,x_column='settle_date',yaxis2_cols=['close'],
                      y_left_label='iv_skew',y_right_label='close',plot_title=chart_title)
    return fig_skew_vs_atm_iv,fig_skew_vs_close
    
def plot_atm_vs_close(SYMBOL_TO_RESEARCH,df_iv_final_in,df_cash_futures_in,year=None):
    # Step 00: select only SYMBOL_TO_RESEARCH from DataFrames 
    df_iv_final = df_iv_final_in[df_iv_final_in.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
    df_cash_futures = df_cash_futures_in[df_cash_futures_in.symbol.str.slice(0,2)==SYMBOL_TO_RESEARCH].copy()
    
    year = 'all' if year is None else year
    if str(year).lower() != 'all':
        y = int(str(year))
        beg_year = y*100*100+1*100+1
        end_year = y*100*100+12*100+31
        df_iv_final = df_iv_final[(df_iv_final.settle_date>=beg_year) & (df_iv_final.settle_date<=end_year)]
        df_cash_futures = df_cash_futures[(df_cash_futures.settle_date>=beg_year) & (df_cash_futures.settle_date<=end_year)]

    print(f'plot_atm_vs_close year: {year}')
    
    # Step 01: create atm implied vol table, that also has the cash price for each settle_date
    df_atmv = df_iv_final[['settle_date','atm_iv']].drop_duplicates()
    df_cf = df_cash_futures[df_cash_futures.symbol==f'{SYMBOL_TO_RESEARCH}Z99']
    df_atmv = df_atmv.merge(df_cf[['settle_date','close']],how='inner',on='settle_date')

    # Step 02: plot atm_iv vs close
    chart_title = f'{SYMBOL_TO_RESEARCH} atm vol vs close'
    df_atm_vs_close = df_atmv[['settle_date','atm_iv','close']]
    fig_atm_vs_close = plotly_plot(df_atm_vs_close,x_column='settle_date',yaxis2_cols=['close'],
                      y_left_label='atm_iv',y_right_label='close',plot_title=chart_title)
    return fig_atm_vs_close

iplot(plot_atm_vs_close('CL',df_iv_final,df_cash_futures,year=2020))
for d in [.05,.1,.2]:
    fig1,fig2 = plot_skew_vs_atm('CL',df_iv_final,df_iv_skew,df_cash_futures,dist_from_zero=d,year=2020)
    iplot(fig1)
    iplot(fig2)


# ### Define initial banner and dropdowns

# In[ ]:


logger = dgc.init_root_logger('logfile.log','WARN') 

# you need to define some css styles as well
STYLE_TITLE={
    'line-height': '20px',
    'textAlign': 'center',
    'background-color':'#47bacc',
    'color':'#FFFFF9',
    'vertical-align':'middle',
} 


    

def get_all_years_per_product(prod,df):
    df2 = df.copy()
    df['prod'] = df.symbol.apply(lambda v: v[:(len(v)-3)])
#     df_this_prod = df_cash_futures[df_cash_futures.symbol.str.slice(0,2)=='CL']
    df_this_prod = df_cash_futures[df_cash_futures.symbol.str.slice(0,2)==prod]
    years = df_this_prod.settle_date.astype(str).str.slice(0,4).astype(int).unique()
    return years.tolist()

top_div = html.Div([
                    dgc.dcc.Markdown('''
# Commodity Option Skew Analysis
## Select a Commodity, Year and Monthcode below to display charts showing:

* atm vol vs price
* skew vs price
* skew vs atm vol
                    '''
                    ,style={'color':'white'})
            ],
            style=STYLE_TITLE,id='top_div')


dropdown_instructions = dgc.DivComponent('dd_instructions',initial_children=['Select from the Product, Year and Month Dropdowns'])

chained_dd_prods = dgc.ChainedDropDownDiv('chained_dd_prods',
                initial_dropdown_labels=['WTI Crude','Brent Crude','Emini'],
                initial_dropdown_values=['CL','CB','ES'],logger=logger)

def _chained_years(inputs):
    prod = inputs[1]
    if prod is None or len(prod)<1:
        return []
    print(prod)
    yyyys = get_all_years_per_product(prod,df_cash_futures)
    choices = [{'label':'all','value':'all'}]  + [{'label':str(yyyy),'value':str(yyyy)} for yyyy in yyyys]
    return  choices

    
chained_dd_years = dgc.ChainedDropDownDiv('chained_dd_years',
                dropdown_input_components=[chained_dd_prods],
                choices_transformer_method=_chained_years,
                placeholder="Select a year",logger=logger)


# ### Build Storage components to store plotly Figures that turn into graphs

# In[ ]:


# define a storage components
#  build a store here
SKEW_RANGE_LIST = [.05,.1,.2]
def create_dropdown_dict_closure(df_iv_final_in, df_iv_skew_in,df_cash_futures_in):
    def _create_dropdown_dict(input_list):
        print(f'create_input_store_dict {input_list}')
        if input_list is None or len(input_list)<2 or (input_list[0] is None and input_list[1] is None):
            return {}
        sym_to_plot = input_list[0]
        year_to_plot = 'all' if input_list[1] is None else input_list[1]
        all_figs = {}
        fig = plot_atm_vs_close(sym_to_plot,df_iv_final_in,df_cash_futures_in,year=year_to_plot)
        all_figs['atm_vs_close'] = fig
        for d in SKEW_RANGE_LIST:
            fig_skew_vs_atm,fig_skew_vs_price = plot_skew_vs_atm(sym_to_plot,df_iv_final_in,df_iv_skew_in,
                                         df_cash_futures_in,dist_from_zero=d,year=year_to_plot)
            all_figs[f'skew_vs_atm_{d}'] = fig_skew_vs_atm
            all_figs[f'skew_vs_price_{d}'] = fig_skew_vs_price
        return all_figs
    return _create_dropdown_dict

create_dropdown_dict = create_dropdown_dict_closure(df_iv_final, df_iv_skew,df_cash_futures)
store_dropdown_outputs = dgc.StoreComponent('store_dropdown_outputs', 
        [(chained_dd_prods.dcc_id,'data'),(chained_dd_years.dcc_id,'data')],
        create_data_dictionary_from_df_transformer=create_dropdown_dict, logger=logger)


# ### create graph components to display

# In[ ]:



def fig_atm_vol_vs_price(input_list):
#     print(f'fig_atm_vol_vs_price {input_list}')
    if input_list is None or len(input_list)<1 or input_list[0] is None:
            return None
    fig_dict = input_list[0]
    if len(fig_dict)<1:
        return None
    fig = input_list[0]['atm_vs_close']
    return fig


def skew_vs_atm_or_price_closure(dist_from_zero,return_skew=True):
    def skew_vs_atm_or_price(input_list):
        if input_list is None or len(input_list)<1 or input_list[0] is None:
                return None
        fig_dict = input_list[0]
        if len(fig_dict)<1:
            return None
        if return_skew:
            fig = input_list[0][f'skew_vs_atm_{dist_from_zero}']
        else:
            fig = input_list[0][f'skew_vs_price_{dist_from_zero}']
        return fig
    return skew_vs_atm_or_price
    



fig_atm_vol_vs_price = dgc.FigureComponent('fig_atm_vol_vs_price',store_dropdown_outputs,fig_atm_vol_vs_price)

fig_skew_list = []
for d in SKEW_RANGE_LIST:
    dd = str(d).replace('.','_')
    skew_vs_atm_id = f'skew_vs_atm_{dd}'
    fig_skew_list.append(dgc.FigureComponent(skew_vs_atm_id,store_dropdown_outputs,
                                             skew_vs_atm_or_price_closure(d,return_skew=True)))
    price_vs_atm = f'price_vs_atm_{dd}'
    fig_skew_list.append(dgc.FigureComponent(price_vs_atm,store_dropdown_outputs,
                                             skew_vs_atm_or_price_closure(d,return_skew=False)))

    
    


# In[ ]:


app_component_list = [top_div,chained_dd_prods,chained_dd_years,store_dropdown_outputs,fig_atm_vol_vs_price] + fig_skew_list
gtcl = ['1fr','49.7% 49.7%','100%','100%'] + ['100%' for _ in range(len(fig_skew_list))]
app_to_use = dgc.dash.Dash(url_base_pathname=configs['url_base_pathname'])
app = dgc.make_app(app_component_list,grid_template_columns_list=gtcl,app=app_to_use)    


# In[ ]:


app.run_server(host=configs['host'],port=int(str(configs['port'])))


# ### Uncomment out the cell below to create a .py file to run this code on a server

# In[ ]:


# !jupyter nbconvert --to script dgrid_components_futures_skew_example_app.ipynb
        


# ## End
