'''
Created on Jul 21, 2019

Define classes that inherit dgrid.ComponentWrapper.  
1. These classes facilitate use of:
    dash_core_components
    dash_html_components
2. They free the developer from having to implement their own callbacks
     on dash_core_components instances.
3. They make it easy to place dash_core_components in a flexible grid.

@author: bperlman1
'''

import dash
import sys,os
if  not os.path.abspath('./') in sys.path:
    sys.path.append(os.path.abspath('./'))
if  not os.path.abspath('../') in sys.path:
    sys.path.append(os.path.abspath('../'))
sys.path.append(os.path.abspath('../../dashgrid'))
sys.path.append(os.path.abspath('../../dashgrid/dashgrid'))
from dashgrid import dgrid
from dashgrid import logger_init as li
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output,State
import dash_table
import pandas as pd
import numpy as np

import traceback

import plotly.graph_objs as go
from plotly.graph_objs.layout import Font,Margin

DEFAULT_LOG_PATH = './logfile.log'
DEFAULT_LOG_LEVEL = 'DEBUG'

#*********************** define useful css styles ***********************
borderline = 'none' #'solid'
button_style={
    'line-height': '40px',
    'borderWidth': '1px',
    'borderStyle': borderline,
    'borderRadius': '1px',
    'textAlign': 'center',
    'background-color':'#fffff0',
    'vertical-align':'middle',
}
button_style_no_border={
    'line-height': '40px',
    'textAlign': 'center',
    'background-color':'#fffff0',
    'vertical-align':'middle',
}

border_style={
    'line-height': '40px',
    'border':borderline + ' #000',
    'textAlign': 'center',
    'vertical-align':'middle',
}

table_like = {
    'display':'table',
    'width': '100%'
}

# define h4_like because h4 does not play well with dash_table
h4_like = { 
    'display': 'table-cell',
    'textAlign' : 'center',
    'vertical-align' : 'middle',
    'font-size' : '16px',
    'font-weight': 'bold',
    'width': '100%',
}


# ************************* define useful factory methods *****************
def create_dt_div(dtable_id,df_in=None,
                  columns_to_display=None,
                  editable_columns_in=None,
                  title='Dash Table'):
    '''
    Create an instance of dash_table.DataTable, wrapped in an dash_html_components.Div
    
    :param dtable_id: The id for your DataTable
    :param df_in:     The pandas DataFrame that is the source of your DataTable (Default = None)
                        If None, then the DashTable will be created without any data, and await for its
                        data from a dash_html_components or dash_core_components instance.
    :param columns_to_display:    A list of column names which are in df_in.  (Default = None)
                                    If None, then the DashTable will display all columns in the DataFrame that
                                    it receives via df_in or via a callback.  However, the column
                                    order that is displayed can only be guaranteed using this parameter.
    :param editable_columns_in:    A list of column names that contain "modifiable" cells. ( Default = None)
    :param title:    The title of the DataFrame.  (Default = Dash Table)
    '''
    
    # create list that 
    editable_columns = [] if editable_columns_in is None else editable_columns_in
    datatable_id = dtable_id
    dt = dash_table.DataTable(
        page_current= 0,
        page_size= 100,
        filter_action='none', # 'fe',
        style_cell_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ] + [
            {
                'if': {'column_id': c},
                'textAlign': 'left',
            } for c in ['symbol', 'underlying']
        ],

        style_as_list_view=False,
        style_table={
            'maxHeight':'450px','overflowX': 'scroll','overflowY':'scroll'
#             'height':'15','overflowX': 'scroll','overflowY':'scroll'
        } ,
        editable=True,
        css=[{"selector": "table", "rule": "width: 100%;"}],
        id=datatable_id
    )
    if df_in is None:
        df = pd.DataFrame({'no_data':[]})
    else:
        df = df_in.copy()
        if columns_to_display is not None:
            df = df[columns_to_display]                
    dt.data=df.to_dict("rows")
    dt.columns=[{"name": i, "id": i,'editable': True if i in editable_columns else False} for i in df.columns.values]                    
    print(f'dt.columns {dt.columns}')
    s = h4_like
    child_div = html.Div([html.Div(html.Div(title,style=s),style=table_like),dt])
    return child_div

def file_store_transformer(contents):
    '''
    Convert the contents of the file that results from use of dash_core_components.Upload class.  
        This method gets called from the UploadComponent class callback.
    :param contents:    The value received from an update of a dash_core_components.Upload instance.'
                            
    '''
    if contents is None or len(contents)<=0 or contents[0] is None:
        d =  None
    else:
        d = dgrid.parse_contents(contents).to_dict('rows')
    return d


def plotly_plot(df_in,x_column,plot_title=None,
                y_left_label=None,y_right_label=None,
                bar_plot=True,figsize=(16,10),
                number_of_ticks_display=20,
                yaxis2_cols=None):
    '''
    Create a plotly.graph_objs.Graph figure.  The caller provides a Pandas DataFrame,
        and an column name for x values.  The y values come from all remaining columns.
    
    :param df_in:    Pandas DataFrame that has an x and multiple y columns.
    :param x_column:    DataFrame column that holds x axis values
    :param plot_title:    Title of Graph.
    :param y_left_label:    left y axis label
    :param y_right_label:    right y axis label
    :param bar_plot:    If True, create a Bar plot figure.  Otherwise, create a Scatter figure.
    :param figsize:    like the matplotlib figsize parameter
    :param number_of_ticks_display:    The number of x axis ticks to display. (Default = 20)
    :param yaxis2_cols:    A list of columns that contain y values that will be graphed 
                            versus the left y axis.
    '''
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

def make_chart_html(figure_id,df,x_column,**kwdargs):
    '''
    Create a dash_html_components.Div wrapper of the dash_core_components.Graph instance.
    
    :param figure_id:    The id parameter of the plotly.graph_objs.Figure instance, that
                            get's created by plotly_plot, that you will display.
    :param df:    DataFrame that will act as input to a call of plotly_plot to create a
                    plotly.graph_objs.Graph figure.
    :param x_column:    Column that holds x values, used in call to plotly_plot.
    '''
    f = go.Figure()
    if df is not None and len(df)>0:
        f = plotly_plot(df,x_column,**kwdargs)
    gr = dcc.Graph(
            id=figure_id,
            figure=f,               
            )
    gr_html = html.Div(
        gr,
        className='item1',
        style={'margin-right':'auto' ,'margin-left':'auto' ,
               'height': '98%','width':'98%','border':'thin solid'},
        id = f'{figure_id}_html'
    )
    return gr_html


def flatten_layout(app):
    # define recursive search
    def _recursive_div_display(c,div_list):
    #     pdb.set_trace()
        if  hasattr(c,'children') and 'div.div' in str(type(c)).lower() and len(c.children)>0:
            for c2 in c.children:
                _recursive_div_display(c2,div_list)
        else:
            div_list.append(c)
    
    # run recursive search
    final_list = []
    for c in list(np.array(app.layout.children).reshape(-1)):    
        dlist = []
        _recursive_div_display(c,dlist)
        final_list.extend(dlist)
    
    # return results
    return final_list
    
    
# ************************ Define the classes that inherit dgrid.ComponentWrapper ************************
class DivComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,input_component=None,
                 input_component_property='data',
                 initial_children=None,
                 callback_input_transformer=None,
                 style=None,logger=None):
        s = {} if style is None else style
        init_children = [] if initial_children is None else initial_children
        h1 = html.Div(init_children,id=component_id,style=s)
        h1_lambda = (lambda v:[v]) if callback_input_transformer is None else callback_input_transformer
        input_tuple = None if input_component is None else [(input_component.id,input_component_property)]
        super(DivComponent,self).__init__(
                    h1,input__tuples=input_tuple,
                    output_tuples=[(h1.id,'children')],
                    callback_input_transformer=h1_lambda,
                    style=s,
                    logger=logger)
        

class UploadComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,text=None,style=None,logger=None):
        t = "Choose a File" if text is None else text
        self.component_id = component_id
        u1 = dcc.Upload(
                    id=component_id,
                    children=html.Div([t]),
                    # Allow multiple files to be uploaded
                    multiple=False,
                    style=button_style if style is None else style)
        
        u1_lambda = lambda value_list: [None] if value_list[0] is None else [file_store_transformer(value_list[0])]
        self.s1 = dcc.Store(id=component_id+"_store")
        super(UploadComponent,self).__init__(
                    u1,input__tuples=[(u1.id,'contents')],
                    output_tuples=[(self.s1.id,'data')],
                    callback_input_transformer=u1_lambda,logger=logger)
        
    @dgrid.ComponentWrapper.html.getter
    def html(self):
        return html.Div([self.div,self.s1])

class UploadFileNameDiv(DivComponent):
    def __init__(self,component_id,upload_component):
        super(UploadFileNameDiv,self).__init__(component_id,upload_component,
                input_component_property='filename',
                style=button_style,
                callback_input_transformer=lambda v: [f'Uploaded File: {v}'])
    
    
class DashTableComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,df_initial,input_component=None,title=None,
                 editable_columns=None,style=None,logger=None):
        
        self.logger = li.init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger
        # add component_id and html_id to self
        self.component_id = component_id
        self.html_id = self.component_id+'_html'
        
        default_data_store = []
        if input_component is None:
            dcs_id = f'{component_id}_default_store'
            dcs_data = None if df_initial is None else df_initial.to_dict('records')
            default_data_store.append(dcc.Store(id=dcs_id,data=dcs_data))
            input_tuples = [(dcs_id,'data')]
        else:
            input_tuples = [input_component.output_data_tuple]
        
        # create initial div
        dtable_div = create_dt_div(component_id,df_in=df_initial,
                        columns_to_display=df_initial.columns,
                        editable_columns_in=editable_columns,
                        title='Dash Table' if title is None else title)
        
        dt_children = [dtable_div] + default_data_store
        outer_div = html.Div(dt_children,id=self.html_id,
                style={
                'margin-right':'auto' ,'margin-left':'auto' ,
                'height': '98%','width':'98%','border':'thin solid'})
        if style is not None:
            for k in style:
                outer_div.style[k] = style[k]
        
        # define dash_table callback using closure so that you don't refer back to 
        #   class instance during the callback
        def _create_dt_lambda(component_id,cols,editable_cols,logger):
            def _dt_lambda(value_list): 
                logger.debug(f'dt_lambda value_list: {value_list}')
                ret = [None,None]
                try:
                    if value_list[0] is not None:
                        dict_df = value_list[0]
                        df = pd.DataFrame(dict_df)
                        dt_div = create_dt_div(component_id,df_in=df,
                                    columns_to_display=cols,
                                    editable_columns_in=editable_cols)
                        ret =  [dt_div,dict_df]
                except Exception as e:
                    logger.warn(str(e))
                logger.debug(f'dt1_lambda ret: {ret}')
                if ret[0] is None:
                    raise ValueError('dt1_lambda value_list has no data.  Callback return is ignored')
                return ret
            return _dt_lambda
        
        
        # do super, but WITHOUT the callback
        super(DashTableComponent,self).__init__(outer_div,
                     input__tuples=input_tuples,
                     output_tuples=[
                         (outer_div.id,'children'),
                         (self.component_id,'data')],
                     callback_input_transformer=lambda v:[None],logger=logger)

        # set the id of this class instance because the input component 
        #   to the super constructor is NOT the main dcc component
        self.id = component_id
        
        # define callback so that it includes self.logger
        dtlam = _create_dt_lambda(self.component_id,df_initial.columns.values,
                                  editable_columns,self.logger)
        self.callback_input_transformer = dtlam
                
class XyGraphComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,input_component,x_column,
                 plot_bars=True,title=None,
                 style=None,logger=None):
        
        self.logger = li.init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger
        # create title
        t = f"Graph {component_id}" if title is None else title
        
        # get input tuple
        input_tuple = input_component.output_data_tuple

        # add component_id and html_id to self
        self.component_id = component_id
        gr_html = make_chart_html(component_id,None,x_column,plot_title=t)

        # define dash_table callback using closure so that you don't refer back to 
        #   class instance during the callback
        def _create_gr_lambda(component_id,x_column,plot_title,logger):
            def gr_lambda(value_list): 
                logger.debug(f'{component_id} gr_lambda value_list: {value_list}')
                ret = [None]
                try:
                    if value_list[0] is not None:
                        df = pd.DataFrame(value_list[0])
                        fig = plotly_plot(df,x_column,plot_title=plot_title,bar_plot=plot_bars)
                        print(f'gr_lambda {fig}')
                        ret =  [fig]
                except Exception as e:
                    traceback.print_exc()
                    logger.warn(f'gr_lambda ERROR:  {str(e)}')
                logger.debug(f'{component_id} gr_lambda ret: {ret}')
                if ret[0] is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    raise ValueError(err_mess)
                return ret
            return gr_lambda

        # set the outer html id
        if style is not None:
            gr_html.style = style
        # do super, but WITHOUT the callback
        super(XyGraphComponent,self).__init__(gr_html,
                     input__tuples=[input_tuple],
                     output_tuples=[(self.component_id,'figure')],
                     callback_input_transformer=lambda v:[None])
        
        # define callback so that it includes self.logger
        gr_lam = _create_gr_lambda(self.component_id,x_column,t,self.logger)
        self.callback_input_transformer = gr_lam
        
class GraphComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,input_component,x_column,y_columns,
                 plot_bars=True,title=None,
                 style=None,logger=None):
        self.logger = li.init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger
        # create title
        t = f"Graph {component_id}" if title is None else title
        
        # get input tuple
        input_tuple = input_component.output_data_tuple

        # add component_id and html_id to self
        self.component_id = component_id
        gr_html = make_chart_html(component_id,None,x_column,plot_title=t,bar_plot=plot_bars)

        # define dash_table callback using closure so that you don't refer back to 
        #   class instance during the callback
        def _create_gr_lambda(component_id,x_column,plot_title,logger):
            def gr_lambda(value_list): 
                logger.info(f'{component_id} gr_lambda value_list: {value_list}')
                ret = [None]
                try:
                    if value_list[0] is not None:
                        df = pd.DataFrame(value_list[0])
                        fig = plotly_plot(df,x_column,plot_title=plot_title,bar_plot=plot_bars)
                        ret =  [fig]
                except Exception as e:
                    traceback.print_exc()
                    logger.warn(f'gr_lambda ERROR:  {str(e)}')
                logger.debug(f'{component_id} gr_lambda ret: {ret}')
                if ret[0] is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    raise ValueError(err_mess)
                return ret
            return gr_lambda

        # set the outer html id
        if style is not None:
            gr_html.style = style
        # do super, but WITHOUT the callback
        super(GraphComponent,self).__init__(gr_html,
                     input__tuples=[input_tuple],
                     output_tuples=[(self.component_id,'figure')],
                     callback_input_transformer=lambda v:[None])
        
        # define callback so that it includes self.logger
        gr_lam = _create_gr_lambda(self.component_id,x_column,t,self.logger)
        self.callback_input_transformer = gr_lam

class FigureComponent(dgrid.ComponentWrapper):
    def __init__(self,component_id,
                 input_component,
                 create_figure_from_df_transformer,
                 input_component_property='data',
                 figure=None,style=None,logger=None):

        self.logger = li.init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger

        # add component_id and html_id to self
        self.component_id = component_id
        gr_html = make_chart_html(component_id,None,None)

        def _create_gr_lambda(component_id,_figure_from_df_transformer,logger):
            def gr_lambda(value_list): 
                logger.debug(f'{component_id} gr_lambda value_list: {value_list}')
                ret = [None]
                try:
                    if value_list[0] is not None:
                        ret =  [_figure_from_df_transformer(value_list[0])]
                except Exception as e:
                    traceback.print_exc()
                    logger.warn(f'gr_lambda ERROR:  {str(e)}')
                logger.debug(f'{component_id} gr_lambda ret: {ret}')
                if ret[0] is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    raise ValueError(err_mess)
                return ret
            return gr_lambda

        # set the outer html id
        if style is not None:
            gr_html.style = style
        # do super, but WITHOUT the callback
        super(FigureComponent,self).__init__(gr_html,
                     input__tuples=[(input_component.id,input_component_property)],
                     output_tuples=[(self.component_id,'figure')],
                     callback_input_transformer=lambda v:[None])
        
        # define callback so that it includes self.logger
        gr_lam = _create_gr_lambda(self.component_id,create_figure_from_df_transformer,
                                   self.logger)
        self.callback_input_transformer = gr_lam

        
        


