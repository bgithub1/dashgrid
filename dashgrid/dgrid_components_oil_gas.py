#!/usr/bin/env python
# coding: utf-8

# # Example of ```VariableRowDiv```
# Build a volatility skew application that shows multiple graphs using the class ```VariableRowDiv```
# 
# ### Usage:
# 1. Run all of the cells below.  
# 2. On the final cell, the url ```http://127.0.0.1:8500``` will appear. 
# 3. Click on it and another web page will launch that displays the output of the app.

# In[14]:


import sys,os
if  not os.path.abspath('./') in sys.path:
    sys.path.append(os.path.abspath('./'))
if  not os.path.abspath('../') in sys.path:
    sys.path.append(os.path.abspath('../'))

import pandas as pd
import numpy as np
import traceback
import os,sys

from dashgrid import dash_df_components as ddfc
import json
import pathlib
HOME_DIR = pathlib.Path('~')


# ### Create a logger that can be used within all components

logger = ddfc.dgc.init_root_logger()
df_ci = pd.read_csv(os.path.join(HOME_DIR,'downloads/country_indicators.csv'))


choices = [{'label':v,'value':v} for v in ['choice1','choice2']]
rad = ddfc.dgc.RadioItemComponent('rad_comp','radio button',choices,None,labelStyle={'display': 'block'})
rs = ddfc.dgc.RangeSliderComponent('rs_comp','range slider',1,10,5)
dd = ddfc.dgc.MultiDropdownDiv('dd_comp',df_ci,df_ci.columns.values[:-1],use_storage_for_callback=False)

def mycallback(input_dict):
    print(input_dict)
    return [[{'initial_data':json.dumps(input_dict)}]]

# v = ddfc.VariableRowDiv('vdiv',[rad,rs,dd],mycallback,[ddfc.DivStatic],['1fr'])
v = ddfc.VariableRowDiv('vdiv',[rad,rs]+dd.dropdown_list,mycallback,[ddfc.DivStatic],['1fr'])
# v = ddfc.VariableRowDiv('vdiv',dd.dropdown_list,mycallback,[ddfc.DivStatic],['1fr'])



# app = ddfc.dgc.make_app([rad,rs]+v.final_components,grid_template_columns_list=['1fr 1fr']+v.final_layout)
app = ddfc.dgc.make_app([rad,rs]+dd.dropdown_list+v.final_components,grid_template_columns_list=['1fr','1fr','1fr 1fr 1fr']+v.final_layout)
# app = ddfc.dgc.make_app(dd.dropdown_list,grid_template_columns_list=['1fr 1fr 1fr'])
# app = ddfc.dgc.make_app(v.final_components,grid_template_columns_list=v.final_layout)
app.run_server(host='127.0.0.1',port=8500)




