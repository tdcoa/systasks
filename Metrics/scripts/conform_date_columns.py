from multiprocessing.sharedctypes import Value
from pathlib import Path
from datetime import datetime
import sys 
import shutil
import pandas as pd 

from sj_misc import sj_Misc as sjmisc


version = 'v1.1'
# sys.argv = [sys.argv[0], 'csvfilepath: test/workfile_gssresusage_source.csv', 'date_columns: [logdate]', 'backup: False' ]
# sys.argv = [sys.argv[0], 'csvfilepath: test/workfile_gssresusage_source.csv', 'date_columns: [Timestamp]', 'old_date_format: mm/dd/yy hh:mm', 'new_date_format: yyyy-mm-dd hh:mm', 'backup: False']


# use misc logger:
misc = sjmisc(logfilepath='./{logdate}--conform_date_columns.log')
log = misc.log
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

# parse commandlines
args = misc.parse_namevalue_args(sys.argv, 
                                required=['csvfilepath', 'date_columns'],
                                defaults={'old_date_format':'mm/dd/yyyy', 'new_date_format':'yyyy-mm-dd', 'debug':True, 'backup':True, 'stop_on_error':False})
scriptfilepath  = Path(args['scriptfilepath']).resolve()
csvfilepath     = Path(str(args['csvfilepath']).strip()).resolve()   # name of excel / csv file (i.e., "system_cpu.csv")
old_date_format = args['old_date_format'].lower()
new_date_format = args['new_date_format'].lower()
date_columns    = [str(x).strip() for x in list(str(args['date_columns']).lower().replace('[','').replace(']','').split(',')) ]
backup          = str(args['backup']).lower().strip() == 'true' 
debug           = str(args['debug']).lower().strip() == 'true' 
stop_on_error   = str(args['stop_on_error']).lower().strip() == 'true' 

log.debug(f'this filepath = {scriptfilepath}')
log.debug(f'csv filepath = {csvfilepath}')
log.debug(f'old date format = {old_date_format}')
log.debug(f'new date format = {new_date_format}')
log.debug(f'date columns = { str(date_columns) }')

if not csvfilepath.exists():
    errmsg = f'csvfilepath not found: { csvfilepath }'
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please    

def apply_dateformat(inputdate:str) ->str:
    if pd.isnull(inputdate): return None 

    # apply some common-sense checks between inputdate and old_date_format, to catch obvious errors:

    err = False
    inputdate = str(inputdate).strip()
    olddtfmt = misc.translate_simple_dateformat(old_date_format, skip_log = True)
    newdtfmt = misc.translate_simple_dateformat(new_date_format, skip_log = True)

    # fix a few easy mistakes:  remove AM/PM from old format if not present in data
    if str(olddtfmt[-2:]).strip().lower() == '%p' and str(inputdate).strip().lower()[-1:] not in ['a','p','m']:
        olddtfmt = str(olddtfmt)[:-2].strip()

    msg = [f'parse  {inputdate}  using format  {olddtfmt}']
    try:
        dtobj = datetime.strptime(inputdate, olddtfmt)
    except Exception as ex:
        # TODO: surmise_datetime_format()
        msg.append(f' FAILED') 
        err = True 

    if err:
        try: 
            dtobj = datetime.strptime(inputdate, newdtfmt)
            msg.append(f', but data already in new format  {newdtfmt}')
            log.debug( ''.join(msg) )
        except:
            msg.append(f', and new format  {newdtfmt}  FAILED')

            if stop_on_error:
                msg.append(f', ABORTING as stop_on_error = True')
                log.error( ''.join(msg) )
                raise ValueError(''.join(msg))

            msg.append(f' - returning original value, which may cause downstream errors!')
            log.error( ''.join(msg) )

        return inputdate

    rtn = datetime.strptime(inputdate, olddtfmt).strftime(newdtfmt)
    msg.append( f'  into new format  {newdtfmt}  returning  {rtn}')
    log.debug( ''.join(msg) )
    return rtn
    

# make copy of original (just once), for saftey:
oldcsvfilepath = Path(str(csvfilepath)[:-4] + '---backup.csv')
if oldcsvfilepath.exists():
    log.info(f"skipping the backup of original file, since file already exists")
elif not backup:
    log.info(f"skipping the backup of original file, as backup parameter == False")    
else:
    log.info(f"making backup of original file, since this will alter the original file")
    shutil.copy(csvfilepath, oldcsvfilepath)

# load csv into dataframe
log.info('load file into memory as dataframe')
df = pd.read_csv(csvfilepath)
columns_orig_case = df.columns # preserver casing of columns, lest we mess up down-stream processes
df.columns = [c.lower() for c in list(df.columns)]

log.info(f'dropping any rows with NULL LogDate')
df.dropna(subset=['logdate'], inplace = True) # TODO: make this a variable, or, pull this logic into its own process

# modify all requested date columns (that exist)
try:
    for col in date_columns:
        if col in df.columns:
            log.info(f"Applying new date format to column: {col}")
            df[col] = df[col].apply(apply_dateformat)
        else:
            log.info(f"Column not in CSV file: {col}")

    # save .csv
    log.info('Saving file (overwriting)...')
    df.columns = columns_orig_case
    df.to_csv(csvfilepath, index=False)

    log.info('Complete!\n\n')
except Exception as ex:
    log.error(f"Failed while trying to conform dates... try re-formatting date fields in excel and re-starting:\n\t\t{ex}\n\n")
    raise Exception 