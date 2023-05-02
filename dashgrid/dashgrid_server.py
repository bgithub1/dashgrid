import datetime
import pandas as pd

import logging

DEFAULT_LOG_PATH = './logfile.log'
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_CONFIGS = {"PATH_DATA_HOME":"./",
                  "host":"127.0.0.1",
                  "port":8550,
                  "url_base_pathname":"futskew"}

def _new_uuid():
    return str(uuid.uuid1())

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

logger = init_root_logger('logfile.log','INFO') 


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

def get_skew_iv_fut():
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
	#         df_iv_skew = df_iv_skew.append(df_skew.copy())
	#         df_iv_final = df_iv_final.append(df_iv.copy())
	#         df_cash_futures = df_cash_futures.append(df_fut.copy())
	        df_iv_skew = pd.concat([df_iv_skew,df_skew.copy()])
	        df_iv_final = pd.concat([df_iv_final,df_iv.copy()])
	        df_cash_futures = pd.concat([df_cash_futures,df_fut.copy()])
	df_iv_skew = df_iv_skew.rename(columns={c:float(c) for c in df_iv_skew.columns.values if '0.' in c})
	return df_iv_skew,df_iv_final,df_cash_futures



