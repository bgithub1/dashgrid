'''
Created on Mar 5, 2019

Analyze and display risk information for baskets of Stocks.


@author: bperlman1
'''

# Add the folder that contains this module, and it's parent folder to sys.path
#   so that you can import the dgrid module
import sys,os
from dashgrid.dgrid import create_grid
if  not os.path.abspath('./') in sys.path:
    sys.path.append(os.path.abspath('./'))
if  not os.path.abspath('../') in sys.path:
    sys.path.append(os.path.abspath('../'))
from dashgrid import dgrid

#  do rest of imports
import dash
import dash_html_components as html
import pandas as pd
import pandas_datareader.data as pdr
import datetime
import argparse as ap
from flask import redirect


# Create css styles for some parts of the display
STYLE_TITLE={
    'line-height': '20px',
    'borderWidth': '1px',
    'borderStyle': 'dashed',
    'borderRadius': '1px',
    'textAlign': 'center',
    'background-color':'#21618C',
    'color':'#FFFFF9',
    'verticalAlign':'middle',
    'height':'50px'
} 


STYLE_UPGRID = STYLE_TITLE.copy()
STYLE_UPGRID['background-color'] = '#EAEDED'
STYLE_UPGRID['line-height'] = '10px'
STYLE_UPGRID['color'] = '#21618C'

STYLE_DROPDOWN = STYLE_UPGRID.copy()
STYLE_DROPDOWN['display'] = 'inline-block'

def yahoo_fetcher(symbol_list,num_days=100):
    '''
    Get daily securities bars from yahoo
    :param symbol_list: like ['AAPL','SPY','XLV']
    :param num_days: like 100
    '''
    dt_end = datetime.datetime.now()
    dt_beg = dt_end - datetime.timedelta(num_days)
    df_final = None
    for symbol in symbol_list:
        df_temp = pdr.DataReader(symbol, 'yahoo', dt_beg, dt_end)
        # move index to date column, sort and recreate index
        df_temp['date'] = df_temp.index
        df_temp = df_temp.sort_values('date')
        df_temp['symbol'] = symbol
        df_temp.index = list(range(len(df_temp)))
        if df_final is None:
            df_final = df_temp.copy()
        else:
            df_final = df_final.append(df_temp,ignore_index=True)
        df_final.index = list(range(len(df_final)))
    df_final = df_final.sort_values(['symbol','date'])
    return df_final
    

def var_builder(df_portfolio):
    '''
    Build Value At Risk values for each symbol in the 'symbol' column in the DataFram df_portfolio
    :param df_portfolio:

    '''
    
def toy_example(host,port):
    DEFAULT_PORTFOLIO_NAME=  'spdr_stocks.csv'             
    DF_POSITION = pd.read_csv(DEFAULT_PORTFOLIO_NAME)

    # create title for page
    title_div = html.Div([html.H3('Risk Analysis of ETF Options Portfolio')],style=STYLE_TITLE)
    
#     title_grid = dgrid.create_grid(
#         [dgrid.GridItem(title_div),dropdown_nav], num_columns=2, 
#         column_width_percents=[80,19.8])

    # create a span with a file upload button and a div  for the filename
    fnt = lambda fn: html.Div([html.H5(f'YOU ARE VIEWING: {"No csv uploaded yet" if fn is None else fn}',style={'height':'1px'})])     

    up_grid = dgrid.CsvUploadGrid('upload-data',
            display_text=html.Div([html.H5("CLICK TO SELECT A LOCAL CSV",style={'height':'1px'})]),
            file_name_transformer=fnt,style=STYLE_UPGRID)
    dropdown_nav = dgrid.DropDownDiv('dd', 
                            ['E-Mini SP','Nymex Crude','Ice Brent'], 
                             ['ES','CL','CB'],style=up_grid.style)
    
    up_grid2 = dgrid.create_grid(
        up_grid.upload_components+[dropdown_nav],num_columns=3,column_width_percents=[40,40,19.8])
    
    # create a grid table
    columns_to_display=['symbol','position']
    editable_cols = ['position']
    table_header = html.Div(['Position Table'],style={'text-align': 'center'})
    gt1 = dgrid.GridTable('t1',table_header,up_grid.output_tuple,
                     editable_columns=editable_cols,
                     columns_to_display=columns_to_display,
                     input_transformer = lambda dict_df: DF_POSITION if dict_df is None else pd.DataFrame(dict_df))
    
    # create a reactive grid graph
    gr1 = dgrid.GridGraph('g1', 'graph 1',gt1.output_content_tuple,
                          df_x_column='symbol',df_y_columns=['position'],plot_bars=True)

    # combine the table and the graph into the main grid
    main_grid =  dgrid.create_grid([gt1,gr1])

    
    # create the app layout         
    app = dash.Dash()
#     app.layout = html.Div(children=[title_div,up_grid.grid,main_grid])
    app.layout = html.Div(children=[title_div,up_grid2,main_grid])

    # create the call backs
    all_components = up_grid.upload_components + [dropdown_nav,gt1,gr1]
    [c.callback(app) for c in all_components]
    
    # run server
    
    app.run_server(host=host,port=port)
    
    
if __name__ == '__main__':
    parser = ap.ArgumentParser()
    parser.add_argument('--host',type=str,
                        help='host url to run server.  Default=127.0.0.1',
                        default='127.0.0.1')   
    parser.add_argument('--port',type=str,
                        help='port to run server.  Default=8400',
                        default='8500')   
    args = parser.parse_args()
    host = args.host
    port = args.port
    toy_example(host,port)
    