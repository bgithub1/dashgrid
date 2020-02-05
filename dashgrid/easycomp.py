#!/usr/bin/env python
# coding: utf-8

# In[159]:


import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output,State
from dash.exceptions import PreventUpdate
import dash_table
import pandas as pd
import numpy as np
import json
import logging
import datetime
import functools
import random


# In[170]:



names = ["Sarah", "Billy", "Michael"]
names_choices = random.choices(names, weights = [2, 1, 1], k = 20)
days = ["Monday", "Tuesday","Wednesday",'Thursday','Friday']
days_choices = random.choices(days, weights = [2,1,2, 1,1], k = 20)
times = list(range(7,12))
times_choices = random.choices(times, weights = [1,1,1,1,1], k = 20)

df = pd.DataFrame({'name':names_choices,'day':days_choices,'breakfast_time':times_choices})
# print(df.name.unique())
# print(df.day.unique())
# print(df.breakfast_time.unique())

# In[171]:


DEFAULT_LOG_PATH = './logfile.log'
DEFAULT_LOG_LEVEL = 'INFO'

def init_root_logger(logfile=DEFAULT_LOG_PATH,logging_level=DEFAULT_LOG_LEVEL):
    level = logging_level
    if level is None:
        level = logging.DEBUG
    # get root level logger
    logger = logging.getLogger()
    if len(logger.handlers)>0:
        return logger
    logger.setLevel(logging.getLevelName(level))

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)   
    return logger


# In[172]:


logger = init_root_logger(logging_level='DEBUG')


# In[173]:


def stop_callback(errmess,logger=None):
    m = "****************************** " + errmess + " ***************************************"     
    if logger is not None:
        logger.debug(m)
    raise PreventUpdate()


# In[174]:


class  BaseComp():
    def __init__(
                self,
                component,
                input_tuples=None,
                output_tuples=None,
                callback_input_transformer=None,
                style=None,
                logger=None,
                loading_state='cube'
    ):
        self.logger = init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger        
        self.component_id = component.id
        self.component = component
        # do inputs and outputs for callback
        self.input_tuples = [] if input_tuples is None else input_tuples
        self.callback_inputs = [] 
        for t in self.input_tuples:
            o = Input(*t)
            self.callback_inputs.append(o)
        self.output_tuples = [] if output_tuples is None else output_tuples
        self.callback_outputs = []
        for t in self.output_tuples:
            o = Output(*t)
            self.callback_outputs.append(o)

                
        self.html_id = f'{self.component_id}_html'
        self.div = html.Div([self.component],id=self.html_id,
                           style={} if style is None else style)
        def default_callback_input_transformer(v):
            self.logger.info(f'BaseComp default_callback_input_transformer input: {v}')
            return v
        
        self.callback_input_transformer = default_callback_input_transformer if callback_input_transformer is None else callback_input_transformer
    
    @property
    def html(self):
        return self.div           

    def callback(self,theapp):     
        @theapp.callback(
            self.callback_outputs, 
            self.callback_inputs 
            )
        def execute_callback(*inputs_and_states):
            if inputs_and_states is None:
                print(f'stoping callback for id {self.component_id}')
                stop_callback(f'{self.component_id}',self.logger)
            l = list(inputs_and_states)
            self.logger.debug(f'{self.html_id} input: {l}')
            ret = self.callback_input_transformer(l)
            self.logger.debug(f'{self.html_id} output: {ret}')
            return [ret] #if type(ret) is not list else ret
        if len(self.callback_outputs)<=0:
            self.logger.info(f'BaseComp no callback')
            return None     
        return execute_callback
                          

class StoreComp(BaseComp):
    def __init__(self,component_id,input_components,initial_data=None,logger=None):
        def store_comp_callback_closure(input_tuples):
            def sto_cb(input_list):
                ret = {input_tuples[i][0]:input_list[i] for i in range(len(input_tuples))}
                return ret
            return sto_cb
        #  Build the list "its"
        # input_components can be either:
        #  1. instances of BaseComp or
        #  2. actual tuples
        # decide which here
        if type(input_components[0]) == tuple:
            its = input_components
        else:
            # decide if we need to use functools.reduce
            if len(input_components)<2:
                # no we do not
                its = input_components[0].output_tuples
            else:
                # yes we do
                its = functools.reduce(lambda a,b : a.output_tuples+b.output_tuples,input_components)
        component = dcc.Store(component_id) 
        if initial_data is not None:
            component = dcc.Store(component_id,data=[initial_data])
        super().__init__(component,
                            input_tuples = its,
                            output_tuples = [(component_id,'data')],
                            logger=logger,
                            callback_input_transformer=store_comp_callback_closure(its)
        )
        


# In[176]:


class RadioComp(BaseComp):
    def __init__(self,component_id,initial_data=None,**kwargs):
        opts = [{'label':'','value':''}] if  initial_data is None else initial_data
        component = dcc.RadioItems(component_id,options=opts)
        if 'output_tuples' in kwargs:
            super().__init__(component,**kwargs)
        else:
            super().__init__(component,output_tuples=[(component_id,'value')],**kwargs)

class DropdownComp(BaseComp):
    def __init__(self,component_id,initial_data=None,**kwargs):
        opts = [{'label':'','value':''}] if  initial_data is None else initial_data
        component = dcc.Dropdown(component_id,options=opts)
        if 'output_tuples' in kwargs:
            super().__init__(component,**kwargs)
        else:
            super().__init__(component,output_tuples=[(component_id,'value')],**kwargs)

class DivComp(BaseComp):
    def __init__(self,component_id,initial_data=None,**kwargs):
        children = [] if  initial_data is None else initial_data
        component = html.Div(children=children,id=component_id)
        if 'output_tuples' in kwargs:
            super().__init__(component,**kwargs)
        else:
            super().__init__(component,output_tuples=[(component_id,'value')],**kwargs)

def get_class_shortname(type_input):
    return str(type_input).replace('<','').replace('>','').replace("'",'').split('.')[-1]

class ReactiveDivComp(BaseComp):
    def __init__(self,component_id:str,
                 input_components:list,
                 transform_inputs_callback,
                 output_component_types:list,
                 **kwargs):
        self.transform_inputs_callback = transform_inputs_callback
        self.sto_comp = StoreComp(f'store_comp_{component_id}',input_components=input_components)
        
        # create the id's for the components that get created during div_cb
        self.output_children_id_list = []
        for i in range(len(output_component_types)):
            ot = output_component_types[i]
#             self.output_children_id_list.append(str(ot).replace('<','').replace('>','').replace("'",'').split('.')[-1])
            output_type_shortname = get_class_shortname(ot)#str(ot).replace('<','').replace('>','').replace("'",'').split('.')[-1]
            ot_id = f'reactive_div_{output_type_shortname}_{i}'
            self.output_children_id_list.append(ot_id)
        
        # define a callback that will, for do the following:
        #  1. call the user-supplied method transform_inputs_callback
        #  2. loop on each of the output_component_types to:
        #    a. Instantiate a new instance of the type using 
        #            output_component_types[i](component_id,**comp_kwargs)
        #    b. Append the html for the type to the list output_div_children
        #  3. return the list of html children to BaseComp.  BaseComp's component is an html.Div, 
        #        so the children argument of that div will receive the list output_div_children
        def div_cb(input_list):
            print(f"ReactiveDivComp div_cb input_list: {input_list}")
            in_dict = input_list[0]
            if in_dict is None:
                stop_callback('div_cb in_dict is None')
            all_comps_kwargs =  self.transform_inputs_callback(in_dict)
            output_div_children = []
            for i in range(len(output_component_types)):
                output_comp_type = output_component_types[i]
#                 output_type_shortname = self.output_children_id_list[i]
#                 oct_id = f'reactive_div_{output_type_shortname}_{i}'
                oct_id = self.output_children_id_list[i]
                comp_kwargs = all_comps_kwargs[i]
#                 c = output_component_types[i](component_id,**comp_kwargs)
                c = output_comp_type(oct_id,**comp_kwargs)
                output_div_children.append(c.html)
            print(f"ReactiveDivComp div_cb children: {output_div_children}")
            return output_div_children
        
        final_div = html.Div(id=f'final_div_{component_id}')
        super().__init__(final_div,
                   input_tuples = self.sto_comp.output_tuples,
                   output_tuples = [(final_div.id,'children')],
                   callback_input_transformer=div_cb)
        self.div = html.Div([self.div,self.sto_comp.html])

        
    # overrid callback in order to register storage comp
    def callback(self,theapp):
        print(f'reactivediv callback')
        self.sto_comp.callback(theapp)
        super().callback(theapp)
            
            
    


 
def choices_from_df_slice_closure(cols_to_use,index_of_col_to_select,df,component_id,logger):
    def choices_from_df_slice(input_list):
        print(f'choices_from_df_slice {component_id} input_list {input_list}')
        # Step 01: the inputs come in a "funny" order:
        #   -- First, input_list[0] is the current dropdown's current selected item
        #   -- Second, input_list[1:] are the other other inputs
        # Step 02: get a copy of the DataFrame from which you will slice inputs
        dfc = df[cols_to_use].drop_duplicates().copy()
        current_input = 0
        for il in input_list[1:]:
            if il is not None:
                try:                
                    dfc = dfc[dfc[cols_to_use[current_input]]==il]
                except Exception as e:
#                     print(f'choices_from_df_slice {component_id}')
#                     print(f'choices_from_df_slice exception {e}')
#                     print(f'choices_from_df_slice il {il}')
#                     print(f'choices_from_df_slice cols_to_use[current_input] {cols_to_use[current_input]}')
#                     print(f'choices_from_df_slice dfc {dfc}')
                    raise ValueError(e)
                    
            current_input += 1
        unique_values = dfc[cols_to_use[index_of_col_to_select]].unique()
        choices = [{'label':uv,'value':uv} for uv in unique_values]
        return choices
    
    return choices_from_df_slice

class ChainedChoicesComp(DivComp):
    def __init__(self,
                component_id,
                df,
                columns_to_use,
                choices_components_types,
                style=None,
                logger=None):
        # Step 01: save inputs
        self.logger = init_root_logger(DEFAULT_LOG_PATH, DEFAULT_LOG_LEVEL) if logger is None else logger
        self.component_id = component_id
        self.columns_to_use = columns_to_use
        self.choices_components_types  = choices_components_types
        shortnames = [get_class_shortname(c_type) for c_type in choices_components_types]
        self.output_children_id_list = [f'{component_id}_{shortnames[i]}_{i}' for i in range(len(shortnames))]
        # Step 02:  intialize the list of dropdown components that go in the div
        self.output_component_list = []
        # Step 03:  set to all None, and during loop, replace None with
        initial_placeholders = [] 
        # Step 04:  loop through each column, making an instance of dgc.ChainedDropDownDiv 
        for i in range(len(self.columns_to_use)):
            # create a unique id for each dgc.ChainedDropDownDiv
            cc_component_id = self.output_children_id_list[i]
            # use sl_closure to generate a callback for each dgc.ChainedDropDownDiv
            choices_from_df_method = choices_from_df_slice_closure(self.columns_to_use,i,df,cc_component_id,self.logger)
            # call the callback once to obtain intial dropdown lists
            initial_choices = choices_from_df_method([None] + initial_placeholders )
#             # from initial choices, get intial labels (which will also be used as values)
#             initial_labels = [v['label'] for v in initial_choices]
            # use the first lable as the placeholder input to each dgc.ChainedDropDownDiv
            initial_placeholders.append(initial_choices[0]['label'])
            # create an instance of dgc.ChainedDropDownDiv for this column in self.columns_to_use
#             choices = [{'label':v,'value':v} for v in initial_labels]
            comp_type = choices_components_types[i]
            if i<1:
                cdd = comp_type(
                    cc_component_id,
                    initial_data = initial_choices)
            else: 
                cdd =  comp_type(
                    cc_component_id,
                    initial_data = initial_choices,
                    input_tuples = [(oc.component_id,'value') for  oc in self.output_component_list],
                    output_tuples = [(cc_component_id,'options')],
                    callback_input_transformer = choices_from_df_method)
            # append the newly created instance to the instance's dropdown_list
            self.output_component_list.append(cdd)
            
        super().__init__(component_id,initial_data=self.output_component_list)
#         self.div = html.Div(children=[self.div]+[c.html for c in self.output_component_list])
        self.div = html.Div(children=[c.html for c in self.output_component_list])

    # overide the callback of dgc.DivComponent so that you register all of the 
    #   ChainedDropDownDiv's
    def callback(self,theapp):  
#         super().callback(theapp)
        for d in self.output_component_list:
            d.callback(theapp)


# In[192]:


def make_app(base_comp_children):
    all_html = [c.html for c in base_comp_children]

    main_div = html.Div(all_html)
    app  = dash.Dash()
    app.layout=main_div

    for c in base_comp_children:
        try:
            if hasattr(c, 'route'):
                c.route(app)
            if isinstance(c, BaseComp):
                c.callback(app)
        except Exception as e:
            print(e)
    return app

# create MultiComp
# has inputs, a store, and outputs

fruit_comp = RadioComp('fruit1',initial_data=[{'label':v,'value':v} for v in ['strawberries','blueberries','pears']])
cereal_comp = DropdownComp('cereal1',initial_data=[{'label':v+' Flakes','value':v + ' Flakes'} for v in ['Bran','Corn','Oat']])

def transform_food(in_dict):
    fruit = in_dict['fruit1']
    cereal = in_dict['cereal1']
    div1 = f'First I pour my {cereal}'
    div2 = f'Then I throw in  my {fruit}'
    div3 = f"So, for breakfast I have {fruit} in my {cereal}"
    return [{'initial_data':div1},{'initial_data':div2},{'initial_data':div3}]
    
div_comp = ReactiveDivComp('div1',
                [fruit_comp,cereal_comp],
                 transform_inputs_callback=transform_food,
                 output_component_types=[DivComp,DivComp,DivComp]
)



multi_div_comp = ChainedChoicesComp('multi_div',df,['name','day','breakfast_time'],[DropdownComp]*3)

# all_children = [fruit_comp,cereal_comp,div_comp]
all_children = [multi_div_comp]
app = make_app(all_children)
app.run_server(host='127.0.0.1',port=8500)


