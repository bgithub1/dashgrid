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
# import traceback
# import pdb

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
                 input_storage_component:dgc.ComponentWrapper,
                 storage_key:str,
                 initial_data:pd.DataFrame=None,
                 title:str=None,
                 editable_columns:list=None,
                 style:dict=None,
                 logger:dgc.logging.Logger=None,
                 columns_to_round:list=None,
                 digits_to_round=2,
                 title_style:dict=None):
        
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
    def __init__(self,component_id:str,
                 initial_data=None,
                 **kwargs):
        self.kwargs_for_clone = kwargs.copy()
        self.kwargs_for_clone['initial_data'] = initial_data
        super(TableInput,self).__init__(component_id, None, None,initial_data=initial_data,**kwargs)

    def clone(self,component_id,**kwargs):
        if kwargs is not None:
            print(f'TableInput.clone kwargs: {kwargs.keys()}')
        new_kwargs = kwargs.copy()        
        for kwa in self.kwargs_for_clone.keys():
            if kwa not in new_kwargs.keys():
                new_kwargs[kwa] = self.kwargs_for_clone[kwa]
        return TableInput(component_id,**new_kwargs)
    

        
# ************************ Define the classes that inherit dgrid.ComponentWrapper ************************
def make_col_args(df,y_left_label=None,y_right_label=None,use_yaxis2=False):
    if df is None:
        return {a:None for a in ['x_column','yaxis2_cols','y_left_label','y_right_label']}
    cols = df.columns.values
    x_col = cols[0]
    yaxis2_cols = None
    yll = cols[1] + ' values' if y_left_label is None else y_left_label
    yrl = y_right_label
    if len(cols)>2 and use_yaxis2:
        yaxis2_cols = cols[2:]
        if yrl is None:
            yrl = ','.join(yaxis2_cols) + ' values'
    return {'x_column':x_col,'yaxis2_cols':yaxis2_cols,'y_left_label':str(yll),'y_right_label':yrl}    

class XyGraphFromStore(ComponentFromStore):
    def __init__(self,component_id,
                 input_storage_component,
                 storage_key,
                 x_column=None,
                 initial_data=None,
                 title=None,
                 plot_bars=False,
                 y_left_label=None,
                 y_right_label=None,
                 use_yaxis2=False,
                 logger=None,
                 marker_color=None,
                 number_of_ticks_display=20,
                 style=None):
        
#         self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger
        # create title
        self.plot_title = f"Graph {component_id}" if title is None else title
        
        # add component_id and html_id to self
        self.component_id = component_id
#         gr_html = dgc.make_chart_html(component_id,initial_data,
#                     x_column,plot_title=self.plot_title,marker_color=marker_color,bar_plot=plot_bars)
        
        col_args =  make_col_args(initial_data,y_left_label=y_left_label,
                        y_right_label=y_right_label,use_yaxis2=use_yaxis2) 
    
        gr_html = dgc.make_chart_html(
            component_id,
            initial_data,
            col_args['x_column'],
            yaxis2_cols=col_args['yaxis2_cols'],
            y_left_label=col_args['y_left_label'],
            y_right_label=col_args['y_right_label'],
            plot_title=title,
            bar_plot=plot_bars,
            number_of_ticks_display=number_of_ticks_display,
            marker_color=marker_color)
            
        self.plot_bars = plot_bars
        self.storage_key = storage_key
        # set the outer html id
        gr_html.style = dgc.border_style if style is None else style
        
        def callback_closure(x_column=col_args['x_column'],
            yaxis2_cols=col_args['yaxis2_cols'],
            y_left_label=col_args['y_left_label'],
            y_right_label=col_args['y_right_label'],
            plot_title=title,
            bar_plot=plot_bars,
            number_of_ticks_display=number_of_ticks_display,
            marker_color=marker_color):
        
            def callback_from_storage(input_list_with_storage_dict):
#                     return [None]
                df = dataframe_from_storage(input_list_with_storage_dict,self.storage_key,self.component_id)
                if df is None:
                    err_mess = f'{component_id} gr_lambda IGNORING callback. NO ERROR'
                    dgc.stop_callback(err_mess,self.logger)
#                 fig = dgc.plotly_plot(df,x_column,
#                         plot_title=self.plot_title,bar_plot=plot_bars,marker_color=marker_color)
                fig = dgc.plotly_plot(df,
                                      x_column,yaxis2_cols=yaxis2_cols,
                                      y_left_label=y_left_label,
                                      y_right_label=y_right_label,
                                      plot_title=plot_title,
                                      bar_plot=bar_plot,
                                      number_of_ticks_display=number_of_ticks_display,
                                      marker_color=marker_color)
                ret =  [fig]
                return ret
            return callback_from_storage   
        cb = callback_closure(
            col_args['x_column'],
            yaxis2_cols=col_args['yaxis2_cols'],
            y_left_label=col_args['y_left_label'],
            y_right_label=col_args['y_right_label'],
            plot_title=title,
            bar_plot=plot_bars,
            number_of_ticks_display=number_of_ticks_display,
            marker_color=marker_color)
        
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
            
class FigureStatic(dgc.FigureComponent):
    def __init__(self,component_id,
                 figure,
                 style=None,logger=None,
                 **kwargs):

        self.kwargs_for_clone = kwargs.copy()
        self.kwargs_for_clone['figure'] = figure
        self.kwargs_for_clone['style'] = style
        self.kwargs_for_clone['logger'] = logger
        
        self.logger = dgc.init_root_logger(dgc.DEFAULT_LOG_PATH, dgc.DEFAULT_LOG_LEVEL) if logger is None else logger

        # add component_id and html_id to self
        self.component_id = component_id
#         gr_html = dgc.make_chart_html(component_id,None,None)
        self.figure = figure
        if 'initial_data' in kwargs.keys():
            self.figure = kwargs['initial_data']
        # set the outer html id
#         gr_html.style = dgc.border_style if style is None else style
        # do super, but WITHOUT the callback
#         pdb.set_trace()
        super(FigureStatic,self).__init__(self.component_id,
                    None,
                    None,
                    figure=self.figure,
                     style=style,
                     logger=logger)

    def clone(self,component_id,**kwargs):
        if kwargs is not None:
            print(f'FigStatic.clone kwargs: {kwargs.keys()}')
        new_kwargs = kwargs.copy()        
        for kwa in self.kwargs_for_clone.keys():
            if kwa not in new_kwargs.keys():
                new_kwargs[kwa] = self.kwargs_for_clone[kwa]
        return FigureStatic(component_id,**new_kwargs)
        
        
class TextBoxInput(dgc.InputBox):
    def __init__(self,component_id,**kwargs):
        super(TextBoxInput,self).__init__(component_id,kwargs)
        self.initial_data = self.input_component.placeholder              

DEFAULT_COMPONENT_TRANSFORM_DICT = {
    str(TableInput):dgc.make_df,
    str(TextBoxInput):str,
    str(FigureStatic):dgc.make_df,
    str(dgc.ChainedDropDownDiv):str,
    str(dgc.RadioItemComponent):str,
    str(dgc.RangeSliderComponent):str,
}


class VariableRowDiv():
    def __init__(self,
            component_id,
            input_component_list,
            app_callback,
            repeating_row_component_template,
            repeating_row_layout_template,
            component_transform_dict=None,
            logger=None):
        '''
        VariableRowDiv allows you to specify a list of "example" components that will get
          repeated in as many rows as you specify in app_callback.
          1. The class holds an instance of dcc.Store, which gets fed data from the input_component_list.
          2. After the dcc.Store gets updated, the user provided app_callback method gets called
               which takes a single dict argument, and returns a 2 dimensional list of data objects
               like DataFrames, dicts, strings, etc.  These data objects are the data that gets
               injected into the visual components that you specify in the repeating_row_component_template
               argument.
        Example:  your repeating_row_component_template = [TableInput,XYGraphSimple].
                  Your app_callback returns 6 DataFrams: [[df1, df1],[df2,df2], [df3,df3]]
                  This will cause 3 rows to display, where each row will have a Dash Table on the
                    left, and a Dash graph on the right
        
        :param component_id: id of final div
        :param input_component_list: a list of instances derived from dgc.ComponentWrapper
                that provide new data, and force invocation of the app_callback and page refresh
        :param app_callback: a user supplied method that takes one argument (a dict) and returns a
                2 dimensional array of objects that can be loaded into the components of the
                repeating_row_component_template
        :param repeating_row_component_template: a list - like [TableInput,XYGraphSimple] that get
                 displayed multiple times, depending on how many inner rows get returned from
                 app_callback
        :param repeating_row_layout_template: a list like [['1fr 1fr']] or [['1fr'],['1fr']] that
                 determines how the components of the repeating_row_component_template get displayed
        :param component_transform_dict: a dictionary of component types vs methods, where each
                 method determines how the data from app_callback get's modified before it is
                 injected into the components of repeating_row_component_template.  If None,
                 the DEFAULT_COMPONENT_TRANSFORM_DICT version is used
        :param logger:
        '''
        # Save the input variables for later use in other methods of the class
        # Save the id, which will be the id of the main Div that this class renders
        self.component_id = component_id
        self.logger = logger if logger is not None else dgc.init_root_logger('logfile.log','INFO')
        # Store the callback
        self.app_callback = app_callback
        
        # Initialize the component_transform_dict
        self.component_transform_dict = DEFAULT_COMPONENT_TRANSFORM_DICT
        if component_transform_dict is not None:
            self.component_transform_dict.update(component_transform_dict)
        self.repeating_row_component_template = repeating_row_component_template
        self.repeating_row_layout_template = repeating_row_layout_template
        
        # Initialize the input tuple of the internal dcc.Store.
        #  The inputs get stored in self.storage_comp.  Then, the Output of self.storage_comp  
        #   causes the DivComponent callback (see make_component_method below) to fire, and
        #   and to create instances of the components in repeating_row_component_template
        self.input_component_list = input_component_list        
        storage_input_tuples = [ic.output_data_tuple for ic in self.input_component_list]
        self.input_component_types = [type(ic) for ic in self.input_component_list]
        self.input_component_ids = [ic.component_id for ic in self.input_component_list]
        
        # the data_converter variable holds a method that will get fired when self.storage_comp get's
        #  updated with new input 
        self.data_converter = self.store_transform_closure()
        # instantiate self.storage_comp
        self.storage_comp = dgc.StoreComponent(f'store_comp_{self.component_id}',
                storage_input_tuples,
                create_data_dictionary_from_df_transformer=lambda v:v,
                initial_data={})
        # Create the method that generates renders the repeating_row_component_template in
        #  the main DivComponent 
        make_component_method = self.make_comps_closure()
        
        # Create the DivComponent, which holds all the repeated rows of repeating_row_component_template
        #   which gets displayed in a single html div 
        self.content_div = dgc.DivComponent('variable_content',
                    input_component=[self.storage_comp.output_data_tuple],
                    callback_input_transformer=lambda input_list:make_component_method(input_list),
                    logger=self.logger)
        
        # Allow a user of the class to reference the 2 components (and their layout) 
        #  that need to be included when dgc.make_app is called
        self.final_components = [self.content_div,self.storage_comp]
        self.final_layout = ['1fr', '0%']

    # closure that creates a method to transform an input_list of values from the input components
    #   to an a dictionary of data, where:
    #     1. the keys of the dictionary are the input component's component_id fields, and
    #     2. the values of the dictionary are data types converted FROM json to something like
    #        a string, a DataFrame, etc.
    def store_transform_closure(self):
        def _store_transform(input_list):
            # validate input_list
            if len(input_list)<1:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',self.logger)            
            if input_list[0] is None:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',self.logger)            
            # initialize output dict
            output_dict = {}
            # loop through each input json in the input_list argument
            for i in range(len(input_list)):
                il = input_list[i]
                ict = str(self.input_component_types[i])
                conv_method = str
                conv_key = ict
                if conv_key in self.component_transform_dict.keys():
                    conv_method = self.component_transform_dict[conv_key]
                else:
                    self.logger.warn(f'store_transform unexpected conv_key: {conv_key}')
                    self.logger.warn(self.component_transform_dict)
                conv_data = None if il is None else conv_method(il)
                cid = self.input_component_list[i].component_id
                output_dict[cid] = conv_data
            return output_dict
        return _store_transform
            
    # this closure returns a method that assembles all of the rows of output component 
    #   in the argument "row_comps", and creates a single html div.
    #   The data_converter argument is a method that gets generated from the store_transform_closure
    #      closure, which gets called in the constructor to VariableRowDiv      
    def make_comps_closure(self):
        # Return this method to caller of make_comps_closure
        def make_comps(input_list):
            '''
            :param input_list: a single element list that holds a dictionary
            '''
            # Convert the 
            input_dict = self.data_converter(input_list[0])
            if len(input_dict)<1:
                dgc.stop_callback(f'store_transform has NO data.  Callback return is ignored',self.logger)            

            # !!!!!!!!!!!! RUN THE USER'S CALLBACK HERE !!!!!!!!!!!!!!!!
            all_rows_data = self.app_callback(input_dict)
            if all_rows_data is None:
                return [dgc.html.Div()]

            all_comps = []
            for i in range(len(all_rows_data)):
                for j in range(len(self.repeating_row_component_template)):
                    # get the component to be replicated
                    comp = self.repeating_row_component_template[j] 
                    # create its component_id
                    cid = f'{self.component_id}r{i+1}c{j+1}'
                    # get the initial_data for the new component
                    data_element = all_rows_data[i][j]
                    # is the data_element ITSELF a dict?
                    if type(data_element) == dict:
                        # if so, then call comp.clone by using the data_elment as kwdargs
                        if type(comp) == type:
                            c = comp(cid,**data_element)
                        else:
                            c = comp.clone(cid,**data_element)
                    else:
                        # just use the data_element as the initial_data argument to clone
                        if type(comp) == type:
                            c = comp(cid,initial_data=data_element,title=cid)
                        else:
                            c = comp.clone(cid,initial_data=data_element,title=cid)
                    all_comps.append(c)
            html_grid = dgc.create_grid(all_comps,row_layout=self.repeating_row_layout_template)
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
        h_string = ''.join(['#' for _ in range(text_size)])
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

class DivStatic(dgc.DivComponent):
    def __init__(self,
                 component_id,
                 initial_data=None,
                 **kwargs):
        self.component_id = component_id
        self.kwargs_for_clone = kwargs.copy()
        self.kwargs_for_clone['initial_data'] = initial_data
        super().__init__(self.component_id, initial_children=initial_data)

    def clone(self,component_id,**kwargs):
        if kwargs is not None:
            print(f'TableInput.clone kwargs: {kwargs.keys()}')
        new_kwargs = kwargs.copy()        
        for kwa in self.kwargs_for_clone.keys():
            if kwa not in new_kwargs.keys():
                new_kwargs[kwa] = self.kwargs_for_clone[kwa]
        return DivStatic(component_id,**new_kwargs)

# *************************** Component examples to use with VariableRowDiv ************
# component examples


