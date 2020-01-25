'''
Created on Jul 21, 2019

Define classes that inherit ComponentWrapper.  
1. These classes facilitate use of:
    dash_core_components
    dash_html_components
2. They free the developer from having to implement their own callbacks
     on dash_core_components instances.
3. They make it easy to place dash_core_components in a flexible grid.

@author: bperlman1
'''

import sys,os
if  not os.path.abspath('./') in sys.path:
    sys.path.append(os.path.abspath('./'))
if  not os.path.abspath('../') in sys.path:
    sys.path.append(os.path.abspath('../'))

from dashgrid import dgrid_components as dgc
import dash_html_components as html
import pandas as pd
import traceback

# ***************************************** Define input components ***********************************

# ***************************************** Define input components ***********************************

# ***************************************** Define component_from_store ***********************************
class ComponentFromStore(dgc.ComponentWrapper):
    def __init__(self,
                 component,
                 component_id,
                 input_storage_component,
                 output_callback,
                 **kwargs):
        logger = None if 'logger' not in kwargs.keys() else kwargs['logger']
        self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger
        self.component_id = component_id
        self.input_storage_component = input_storage_component
        self.output_callback = output_callback
        self.input_data_tuples = [] if input_storage_component is None else [input_storage_component.output_data_tuple]
        if 'initial_data' in kwargs.keys():
            self.initial_data = kwargs['initial_data']
        oc = lambda v:[None] 
        if output_callback is not None:
            oc = output_callback
        super(ComponentFromStore,self).__init__(
                    component,
                    input__tuples=self.input_data_tuples,
                    output_tuples=kwargs['output_tuples'],
                    callback_input_transformer=oc,
                    style=None if 'style' not in kwargs.keys() else kwargs['style'],
                    logger = None if 'logger' not in kwargs.keys() else kwargs['logger'])
    
#     def clone(self,component_id,input_storage_component=None,
#               output_callback=None,**kwargs):
#         icp = self.input_storage_component if input_storage_component is None else input_storage_component
#         oc = self.output_callback if output_callback is None else output_callback
#         kwa = self.kwargs if (kwargs is None) or (len(kwargs)<1) else kwargs
#         arglist = [self.component,component_id,icp,oc,kwa]
#         c = ComponentFromStore(arglist)
#         return c
    
# ***************************************** Define components from store components ***********************************
def dataframe_from_storage(input_list_with_storage_dict,storage_key,component_id=''):
    if input_list_with_storage_dict is None or len(input_list_with_storage_dict)<1:
        return None
    storage_dict = input_list_with_storage_dict[0]
    if type(storage_dict) == list:
        storage_dict = storage_dict[0]
    if storage_dict is None or len(storage_dict)<1:
        return None
    if type(storage_dict) is not dict:
        print(f'dataframe_from_storage component_id: {component_id}')
        return None
    dict_df = storage_dict[storage_key]
    if dict_df is None or len(dict_df)<1:
        return None
    df = dgc.make_df(dict_df)
    return df


class TableFromStore(ComponentFromStore):
    def __init__(self,component_id,
                 input_storage_component,
                 storage_key,
                 initial_data=None,
                 title=None,
                 editable_columns=None,
                 style=None,logger=None,
                 columns_to_round=None,
                 digits_to_round=2,
                 title_style=None):
        
#         self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger
        self.html_id = component_id+'_html'
        self.columns_to_round = columns_to_round
        self.digits_to_round = digits_to_round
        self.title_style = title_style
        self.input_storage_component = input_storage_component
        self.storage_key = storage_key
        self.editable_columns = editable_columns
        self.title = f'Table {component_id}' if title is None else title
        
        init_data = pd.DataFrame() if initial_data is None else initial_data.copy()
        
        dtable_div = dgc.create_dt_div(component_id,df_in=init_data,
                        title=self.title,
                        title_style=self.title_style)
        
        dt_children = [dtable_div]
        outer_div = html.Div(dt_children,id=self.html_id,
                style={
                'margin-right':'auto' ,'margin-left':'auto' ,
                'height': '98%','width':'98%','border':'thin solid'})
        s = dgc.border_style if style is None else style
        for k in s:
            outer_div.style[k] = s[k]
       
        def callback_closure():
            def callback_from_storage(input_list_with_storage_dict):
                df = dataframe_from_storage(input_list_with_storage_dict,self.storage_key,self.component_id)
                if df is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    dgc.stop_callback(err_mess,logger)
                # check if rounding is  necessary
                if self.columns_to_round is not None:
                    df = dgc.dataframe_rounder(df, digits=self.digits_to_round, columns_to_round=self.columns_to_round)
                dt_div = dgc.create_dt_div(component_id,df_in=df,
                        columns_to_display=df.columns.values,
                        editable_columns_in=self.editable_columns,
                        title=self.title,
                        logger=self.logger,
                        title_style=self.title_style)
                dict_df = dt_div.children[1].data
                return [dt_div,dict_df]
#             return None if self.input_storage_component is None else callback_from_storage
            return callback_from_storage
            
        super(TableFromStore,self).__init__(
                    outer_div,
                    component_id,
                    input_storage_component,
                    callback_closure(),
                    output_tuples=[
#                         (outer_div.id,'children')],
                         (outer_div.id,'children'),
                         (component_id,'data')], 
                    initial_data = init_data,                   
                    logger=logger)            
            

class TableInput(TableFromStore):
    def __init__(self,component_id,
                 initial_data=None,
                 **kwargs):
        self.kwargs_for_clone = kwargs.copy()
        self.kwargs_for_clone['initial_data'] = initial_data
        super(TableInput,self).__init__(component_id, None, None,initial_data=initial_data,**kwargs)

    def clone(self,component_id,**kwargs):
        new_kwargs = kwargs.copy()        
        for kwa in self.kwargs_for_clone.keys():
            if kwa not in new_kwargs.keys():
                new_kwargs[kwa] = self.kwargs_for_clone[kwa]
        return TableInput(component_id,**new_kwargs)
        
# ************************ Define the classes that inherit dgrid.ComponentWrapper ************************

class XyGraphFromStore(ComponentFromStore):
    def __init__(self,component_id,
                 input_storage_component,
                 storage_key,
                 x_column,
                 initial_data=None,
                 title=None,
                 plot_bars=False,
                 logger=None,
                 marker_color=None,
                 style=None):
        
#         self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger
        # create title
        self.plot_title = f"Graph {component_id}" if title is None else title
        
        # add component_id and html_id to self
        self.component_id = component_id
        gr_html = dgc.make_chart_html(component_id,initial_data,
                    x_column,plot_title=self.plot_title,marker_color=marker_color,bar_plot=plot_bars)
        self.plot_bars = plot_bars
        self.storage_key = storage_key
        # set the outer html id
        gr_html.style = dgc.border_style if style is None else style
        
        def callback_closure():
            def callback_from_storage(input_list_with_storage_dict):
#                     return [None]
                df = dataframe_from_storage(input_list_with_storage_dict,self.storage_key,self.component_id)
                if df is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    dgc.stop_callback(err_mess,self.logger)
                fig = dgc.plotly_plot(df,x_column,
                        plot_title=self.plot_title,bar_plot=plot_bars,marker_color=marker_color)
                ret =  [fig]
                return ret
            return callback_from_storage   
                
        super(XyGraphFromStore,self).__init__(
                    gr_html,
                    component_id,
                    input_storage_component,
                    callback_closure(),
                    output_tuples=[
                        (self.component_id,'figure')],
                    logger=logger)            
                

class XYGraphSimple(XyGraphFromStore):
    def __init__(self,component_id,
                 initial_data=None,
                 x_column=None,
                 **kwargs):
        self.kwargs_for_clone = kwargs.copy()
        self.kwargs_for_clone['initial_data'] = initial_data
        self.kwargs_for_clone['x_column'] = x_column
        
        super(XYGraphSimple,self).__init__(component_id, None, None,x_column,initial_data=initial_data,**kwargs)
        
    def clone(self,component_id,**kwargs):
        new_kwargs = kwargs.copy()
        for kwa in self.kwargs_for_clone.keys():
            if kwa not in new_kwargs.keys():
                new_kwargs[kwa] = self.kwargs_for_clone[kwa]
        return XYGraphSimple(component_id,**new_kwargs)
                
class FigureStatic(dgc.ComponentWrapper):
    def __init__(self,component_id,
                 figure,
                 style=None,logger=None):

        self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger

        # add component_id and html_id to self
        self.component_id = component_id
        gr_html = dgc.make_chart_html(component_id,None,None)
        self.figure = figure

        # set the outer html id
        gr_html.style = dgc.border_style if style is None else style
        
        # do super, but WITHOUT the callback
        super(FigureStatic,self).__init__(gr_html,
                     input__tuples=[],
                     output_tuples=[(self.component_id,'figure')],
                     callback_input_transformer=lambda _:[dgc.dcc.Graph(id=component_id,figure=self.figure)
])
        
class TextBoxInput(dgc.InputBox):
    def __init__(self,component_id,**kwargs):
        super(TextBoxInput,self).__init__(component_id,kwargs)
        self.initial_data = self.input_component.placeholder              

DEFAULT_COMPONENT_TRANSFORM_DICT = {
    type(TableInput('__id0000__')):dgc.make_df,
    type(TextBoxInput('__id1111')):str
}


class VariableRowDiv():
    def __init__(self,
            app_id,
            input_component_list,
            app_callback,
            repeating_row_component_template,
            repeating_row_layout_template,
            component_transform_dict=None,
            logger=None):
        #
        self.app_id = app_id
        self.logger = logger if logger is not None else dgc.init_root_logger('logfile.log','INFO')
        self.app_callback = app_callback
        ctd = DEFAULT_COMPONENT_TRANSFORM_DICT
        if component_transform_dict is not None:
            ctd.update(component_transform_dict)
        self.repeating_row_component_template = repeating_row_component_template
        self.repeating_row_layout_template = repeating_row_layout_template
        #
        input_comps = input_component_list
        storage_input_tuples = [ic.output_data_tuple for ic in input_comps]
        ic_types = [type(ic) for ic in input_comps]
        ic_ids = [ic.component_id for ic in input_comps]
        stm = self.store_transform_closure(ic_ids,ic_types,ctd,self.logger)
        #
        self.storage_comp = dgc.StoreComponent(f'store_comp_{self.app_id}',
                storage_input_tuples,
                create_data_dictionary_from_df_transformer=lambda v:v,
                initial_data={})
        
        mcc = self.make_comps_closure(self.app_callback,
                     self.repeating_row_component_template,
                     self.repeating_row_layout_template,
                     stm,self.logger)
        self.content_div = dgc.DivComponent('variable_content',
                    input_component=[self.storage_comp.output_data_tuple],
                    callback_input_transformer=lambda input_list:mcc(input_list),
                    logger=self.logger)
        #
        self.final_components = [self.content_div,self.storage_comp]
        self.final_layout = ['1fr', '0%']

    def store_transform_closure(self,input_comp_ids,input_comp_types,transform_dict,logger):
        def _store_transform(input_list):
            if len(input_list)<1:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',logger)            
            if input_list[0] is None:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',logger)            
            output_dict = {}
            for i in range(len(input_list)):
                il = input_list[i]
                ict = input_comp_types[i]
                conv_method = str
                conv_key = ict
                if conv_key in transform_dict.keys():
                    conv_method = transform_dict[conv_key]
                else:
                    logger.warn(f'store_transform unexpected conv_key: {conv_key}')
                conv_data = None if il is None else conv_method(il)
                cid = input_comp_ids[i]
                output_dict[cid] = conv_data
            return output_dict
        return _store_transform
            
            
    def make_comps_closure(self,callback,row_comps,row_layout,data_converter,logger):
        def make_comps(input_list):
            input_dict = data_converter(input_list[0])
            if len(input_dict)<1:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',logger)            

            row_data = callback(input_dict)
            if row_data is None:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',logger)            

            all_comps = []
            gc_list = []
            for i in range(len(row_data)):
                data_for_this_row = row_data[i]
                for j in range(len(row_comps)):
                    comp = row_comps[j] 
                    cid = f'r{i+1}c{j+1}'
                    c = comp.clone(cid,initial_data=row_data[i][j],title=cid)
                    all_comps.append(c)
                gc_list.append(row_layout)
            html_grid = dgc.create_grid(all_comps,len(row_comps))
            return [html_grid]
        return make_comps


# This Markdown component allows you to use markdown in html divs
# create row 1
class MarkdownLine(dgc.dcc.Markdown):
    def __init__(self,
            markdown_text,
            text_size = 0,
            text_color='white',
            text_align='center',
            component_id=None):
        h_string = ''.join(['#' for c in range(text_size)])
        mstring = f'{h_string} {markdown_text}'
        super(MarkdownLine,self).__init__(
            mstring,id=component_id,
            style={'color':text_color,'textAlign': text_align,})
                   
                   
class MarkdownDiv(html.Div):
    def __init__(self,component_id,
                markdown_children_list,
                background_color='#47bacc',
                vertical_align='middle',
                border_style=dgc.border_style,
                line_height='20px',logger=None):
        mstyle={
            'line-height': line_height,
            'background-color':background_color,
            'vertical-align':vertical_align,
            'border-style':border_style
        } 
        super(MarkdownDiv,self).__init__(markdown_children_list,
                    id=component_id,
                    style=mstyle)


