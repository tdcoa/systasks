from pathlib import Path
from datetime import datetime
import sys, shutil
import pandas as pd 

from sj_misc import sj_Misc as sjmisc


version = 'v1.0'
if False:
    sys.argv = [sys.argv[0] 
                ,'csvfilepath: ./test/conform_columns_TEST.csv'
                ,'savefilepath: ./test/conform_columns_TEST--results.csv'
                ,'date_columns: LogTime, Timestamp, LogDate'
                ,'required_columns: LogTime'
                ,'integer_columns: AMPs, CPUs']

# use misc logger:
misc = sjmisc(logfilepath='log/{logdate}--conform_date_columns.log')
log = misc.log
log.info('\n'+('-'*30)+'\n\tNEW RUN\n'+('-'*30))
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

# parse commandlines
args = misc.parse_namevalue_args(sys.argv, 
                                required=['csvfilepath'],
                                defaults={'date_columns':None, 'integer_columns':None, 'required_columns':None, 
                                          'date_format':'yyyy-mm-dd', 'time_format':'hh:mm:ss', 'timestamp_format':'yyyy-mm-dd hh:mm:ss.f',
                                          'integer_error_replace':'NULL', 'savefilepath':None })

scriptfilepath   = Path(args['scriptfilepath']).resolve()
csvfilepath      = Path(str(args['csvfilepath']).strip()).resolve()   # name of excel / csv file (i.e., "system_cpu.csv")
savefilepath     = Path(str(args['savefilepath']).strip()).resolve() if args['savefilepath'] else Path(csvfilepath[:-4] + '--out.csv')
date_columns     = [] if not args['date_columns']     else [str(x).strip() for x in list(str(args['date_columns']).lower().replace('[','').replace(']','').split(',')) ]
integer_columns  = [] if not args['integer_columns']  else [str(x).strip() for x in list(str(args['integer_columns']).lower().replace('[','').replace(']','').split(',')) ]
required_columns = [] if not args['required_columns'] else [str(x).strip() for x in list(str(args['required_columns']).lower().replace('[','').replace(']','').split(',')) ]
date_format      = misc.translate_simple_dateformat(str(args['date_format']).strip(),      skip_log=True) 
timestamp_format = misc.translate_simple_dateformat(str(args['timestamp_format']).strip(), skip_log=True) 
time_format      = misc.translate_simple_dateformat(str(args['time_format']).strip(),      skip_log=True) 
integer_error_replace = str(args['integer_error_replace']).strip() 
if integer_error_replace.lower() in ['none','null','nan','empty']: integer_error_replace = None


log.debug(f'scriptfilepath        = { str(scriptfilepath) }'        )        
log.debug(f'csvfilepath           = { str(csvfilepath) }'           )     
log.debug(f'savefilepath          = { str(savefilepath) }'          )      
log.debug(f'date_columns          = { str(date_columns) }'          )           
log.debug(f'integer_columns       = { str(integer_columns) }'       )         
log.debug(f'required_columns      = { str(required_columns) }'      )          
log.debug(f'date_format           = { str(date_format) }'           )     
log.debug(f'timestamp_format      = { str(timestamp_format) }'      )          
log.debug(f'time_format           = { str(time_format) }'           )     
log.debug(f'integer_error_replace = { str(integer_error_replace) }' )               

date_delims = ['/','-', '.']
time_delims = [':'] 

# initial check if file exists:
if not csvfilepath.exists():
    errmsg = f'csvfilepath not found: { csvfilepath }'
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please    

# load CSV into DataFrame and prep
df = pd.read_csv(csvfilepath)
colmap = [(str(x).strip(), str(x).strip().lower()) for x in list(df.columns)] # map original(0) and lower-case(1) column names
df.columns = [x[1] for x in colmap]  # 0 = original , 1 = lower

# remove any offending records:
for reqcol in required_columns:
    log.info(f'dropping any rows with NULL in {reqcol}')
    df.dropna(subset=[reqcol], inplace = True) 
    
    log.info(f'changing all datatypes to string (easier processing)')
    df=df.applymap(str)



    # ------------------------------------
    # conform datetime columns:
    # ------------------------------------
for datetimecol in date_columns: 
    try:
        datetimecol = datetimecol.strip().lower()
        log.info('\n' + '-'*30 + ' ' + datetimecol.upper())
        log.info(f'Processing date/time row:  { datetimecol }')
        if datetimecol not in df.columns:
            log.warning(f'COLUMN NOT FOUND IN CSV FILE: {datetimecol}')
            continue

        dfdates = df[datetimecol].value_counts()
        dfdates = dfdates.to_frame().reset_index()
        dfdates.columns = [datetimecol, 'date_count']


        # split on space and determine whether we're looking at a date or time, or both:
        log.info('examining delimiters to determine whether date, time, or both (timestamp)')
        sample_value = dfdates.iloc[int(len(dfdates)/2)][datetimecol]
        log.info(f' sampled value: {sample_value}')
        dtdelim = tmdelim = None 
        has_date = has_time = False 
        for d in date_delims:
            if dfdates[datetimecol].str.split(d, expand=False).agg(len).median() > 1.9:
                dtdelim = d 
                has_date = True
                break
        for t in time_delims:
            if dfdates[datetimecol].str.split(t, expand=False).agg(len).median() > 1.9:
                tmdelim = t 
                has_time = True 
                break

        timecol = f'{datetimecol}_time'
        datecol = f'{datetimecol}_date'

        if not has_date and not has_time:
            log.info('structure cannot be recognized as either date nor time, skipping...')
            continue #skip column

        elif has_date and has_time:
            dfdates[datecol] = dfdates[datetimecol].apply(lambda x: str(x).split(' ')[0].strip()) # assumption: date always comes first 
            dfdates[timecol] = dfdates[datetimecol].apply(lambda x: str(x)[str(x).find(' ')+1:].strip()) # everything after the date
            applied_format = timestamp_format
            log.info('structure determined to be TIMESTAMP (date + time, single-space delimited)')

        elif has_date and not has_time:
            dfdates[datecol] = dfdates[datetimecol]
            applied_format = date_format
            log.info('structure determined to be DATE')
            
        elif has_time and not has_date: 
            dfdates[timecol] = dfdates[datetimecol]
            applied_format = time_format
            log.info('structure determined to be TIME')

            
        # DATE LOGIC
        # ----------------------------------------
        current_date_format = ''
        if has_date:
            # use delimiter to split apart date, so we can evaluate the components:
            dfparts = dfdates[datecol].str.split(dtdelim, expand=True)
            dfpartCounts = dfparts.nunique().sort_values()
            dfpartMax = dfparts.max()
            if len(dfpartCounts) != 3: 
                msg = 'date supplied only had 2 parts, requires 3 (d,m,y).  Check your date field and resubmit.'
                log.error(msg)
                raise Exception(msg)

            # define all the parts
            allparts = {}
            for i, (pos, cnt) in enumerate(dfpartCounts.iteritems()):
                allparts[['yr','mth','day'][i]] =  {'pos':pos, 'count':cnt, 'maxvalue':int(dfpartMax[[pos]]) }


                
            
            
            # correct for rare cases where count of month and year are same, then look at max value (max 12 vs max 20 or 2020)
            if allparts['yr']['count'] ==  allparts['mth']['count']  and  allparts['yr']['maxvalue'] < allparts['mth']['maxvalue']: 
                yr_tmp = allparts['yr']
                mth_tmp = allparts['mth']
                allparts['yr'] = mth_tmp 
                allparts['mth'] = yr_tmp


            # assign format strings:
            allparts['yr']['parser']  = '%Y' if len(str(allparts['yr']['maxvalue'])) == 4 else '%y'
            allparts['mth']['parser'] = '%m'
            allparts['day']['parser'] = '%d'
            

            # put it back together into one format
            current_date_format = []
            for pos in sorted([ allparts[n]['pos'] for n in allparts.keys() ]):
                current_date_format.append( {allparts[n]['pos']:allparts[n]['parser'] for n in allparts.keys()}[pos] )
            current_date_format = dtdelim.join(current_date_format)


            
        # TIME LOGIC
        # ----------------------------------------
        current_time_format = ''
        if has_time:
            timedelims_found = round(dfdates[timecol].apply(lambda x: len(str(x).split(tmdelim))).median()) - 1 

            if   timedelims_found == 1:  current_time_format = '%H:%M'
            elif timedelims_found == 2:  current_time_format = '%H:%M:%S'
            else:
                msg = f'bad time format: column  {timecol}  is either missing delimiter ({tmdelim}), or has more than 3 sections (hr, min, sec)'
                log.error(msg)
                raise ValueError(msg) 

            # check for 24 vs 12 hour clock
            hours = dfdates[timecol].apply(lambda x: int(str(x).split(tmdelim)[0])).unique().min()
            if hours.max() > 12: current_time_format = current_time_format.replace('%I','%H') 
            
            # check for fractional seconds:
            fractional_Seconds = round(dfdates[timecol].apply(lambda x: 1 if '.' in x else 0 ).median())
            if fractional_Seconds == 1: current_time_format = current_time_format + '.%f'
        
            # check for AM/PM 
            ampm_found = round(dfdates[timecol].apply(lambda x: 1 if str(x).strip().lower()[-1:] == 'm' else 0).median())
            if ampm_found == 1: current_time_format = current_time_format.replace('%H','%I') + ' %p'
            


        # APPLY LOGIC FOR DATA
        # ----------------------------------------
        def apply_dateformat(inputdate:str) ->str:
            if pd.isnull(inputdate): return None 
            inputdate = str(inputdate).strip()
            msg = [f'    parse  {inputdate}  using format  {current_format} ']

            try:  # Parse old format
                dtobj = datetime.strptime(inputdate, current_format)
            except Exception as ex:
                msg.append(f' FAILED: could not parse date to supplied format, check the csv date format.') 
                log.error(''.join(msg))
                return inputdate 
            
            try:  # Apply new format
                strdate = str(dtobj.strftime(applied_format))
            except Exception as ex:
                msg.append(f' FAILED: bad date_format supplied: {date_format} ')
                log.error(''.join(msg))
                return inputdate

            msg.append(f' and translate to  {applied_format} == {strdate}')
            # log.debug(''.join(msg))
            return strdate 
            

        # Final application of format to data
        # ----------------------------------------
        current_format = f'{current_date_format} {current_time_format}'.strip()
        log.info(f"Parsing data using format  {current_format}  and translating into format  {applied_format}")
        log.info(f"        middle value before change: { df[datetimecol][ int(len(df[datetimecol])/2) -1 ] } ")
        df[datetimecol] = df[datetimecol].apply(apply_dateformat)
        log.info(f"        middle value after change:  { df[datetimecol][ int(len(df[datetimecol])/2) -1 ] } ")
        log.info("Complete!!!")

    except Exception as ex:
        log.exception(f'Something when wrong with conforming date/time column { datetimecol } - check the log: \n\t { misc.logfilepath }')
                


    # ------------------------------------
    # conform integer columns:
    # ------------------------------------
for intcol in integer_columns:    
    try:
        intcol = intcol.strip().lower()
        log.info('\n' + '-'*30 + ' ' + intcol.upper())
        log.info(f'Conforming Integer row:  { intcol }')
        if intcol not in df.columns:
            log.warning(f'COLUMN NOT FOUND IN CSV FILE: {intcol}')
            continue


        def apply_intcheck(inputint:str) ->int:
            try: 
                if '.' in inputint and inputint.split('.')[1] == '0': inputint = inputint.split('.')[0]
                return int(inputint)
            except:
                log.warning(f'non-integer record found: "{ inputint }" -- replacing with  { integer_error_replace }')
                return integer_error_replace

        log.info(f"Replacing any non-integer values in column  {intcol}  with  {integer_error_replace}")
        df[intcol] = df[intcol].apply(apply_intcheck)
        log.info("Complete!!!")

    except Exception as ex:
        log.exception(f'Something when wrong with conforming integer column { datetimecol } - check the log: \n\t { misc.logfilepath }')
                

        

# restore original column case:
df.columns = [x[0] for x in colmap]  # 0 = original , 1 = lower

# save .csv
overwrite = '(overwriting)' if savefilepath.exists() else ''
log.info(f'\n\nSaving file {overwrite} {savefilepath}')
df.to_csv(savefilepath, index=False)
log.info('Complete!')
