from pathlib import Path
from datetime import datetime
from pydoc import resolve
from select import select
import sys, glob, shutil 
from typing import final
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

version = 'v1.1'
# sys.argv = [sys.argv[0],
#              'insertinto_csvfilepath: test/workfile_gssresusage_gtt.csv', 
#              'insertinto_tablename:   APP_TCA_TMP.stg_gss_manual_upload',
#              'selectfrom_csvfilepath: test/workfile_gssresusage_source.csv', 
#              'selectfrom_tablename:   vt_gssresuage_from_csv',
#              "cust_site_id: 'Transcend02'",
#              "AvgIOPsSec: AvgIOPsSecNode",
#              "MaxIOPsSec: MaxIOPsSecNode"
#              ]

# use misc logger:
misc = sjmisc(logfilepath='log/{logdate}--run.log')
log = misc.log
log.info('\n'+('-'*30)+'\n\tMAKESQL - INSERT-SELECT BY COLUMN FUZZY-MATCH\n'+('-'*30))
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

try:
    # parse commandlines
    args = misc.parse_namevalue_args(sys.argv, 
                                    required=[  'insertinto_csvfilepath','selectfrom_csvfilepath',
                                                'insertinto_tablename'  ,'selectfrom_tablename'],
                                    defaults={'sqlinsert_filepath': Path('.') / 'temp' / 'makesql_insert_select.sql', 'debug':False
                                            , 'scriptfilepath':'' })
    scriptfilepath         = Path(args['scriptfilepath']).resolve()
    insertinto_csvfilepath = Path(args['insertinto_csvfilepath']).resolve()
    selectfrom_csvfilepath = Path(args['selectfrom_csvfilepath']).resolve()
    insertinto_tablename   = args['insertinto_tablename']
    selectfrom_tablename   = args['selectfrom_tablename']
    sqlinsert_filepath     = Path(args['sqlinsert_filepath']).resolve() 
    finaltablename         = args['tablename'] if 'tablename' in args else 'vt_csv2vt'
    preworktablename       = finaltablename + '_prework'
    debug                  = str(args['debug']).lower() == 'true'

    # error testing:
    if not insertinto_csvfilepath.exists() or not selectfrom_csvfilepath.exists():
        errmsg = f'required CSV file missing (either or both):\nInsert Into Path: { insertinto_csvfilepath}\nSelect From Path: { selectfrom_csvfilepath }'
        log.error(errmsg)
        log.error(f"\n\n  you're probably missing the mapping file ({ insertinto_csvfilepath }) that defines the structure of the insert.\nThis should be produced by the previous step, so in theory, you should never see this message.  Please explain yourself.\n")
        raise FileNotFoundError()  # hard error please

    sqlinsert_filepath.parent.mkdir(exist_ok=True, parents=True)

    log.debug(f'this filepath = {scriptfilepath}')
    log.debug(f'csv with Insert Into structure = { insertinto_csvfilepath }')
    log.debug(f'csv with Select From structure = { selectfrom_csvfilepath }')
    log.debug(f'Insert Into TableName = { insertinto_tablename }')
    log.debug(f'Select From TableName = { selectfrom_tablename }')
    log.debug(f'SQL-final filepath = { sqlinsert_filepath }')
except Exception as ex:
    log.exception(f'UNHANDLED EXCEPTION in mapping commandline arguments to variables: \n{ex}')
    raise Exception



# load the csvs into df, i=insert, s=select
log.info('opening csv files')
dfi = pd.read_csv(insertinto_csvfilepath)
dfs = pd.read_csv(selectfrom_csvfilepath)
log.info(f'reading column names into memory for comparison')
ins_cols = dfi.columns
sel_cols = dfs.columns
log.info(f'  { insertinto_csvfilepath.name } has { len(ins_cols) } columns')
log.info(f'  { selectfrom_csvfilepath.name } has { len(sel_cols) } columns')
cols = []

# loop thru all Insert columns, and add from select columns where matching, from args, or NULL if missing from both
for col in ins_cols:
    if   col in sel_cols: 
        selvalue = f'"{ col }"' 
    elif col in args:
        scol = str(args[col]).strip()
        if  scol[:1] in ["'"]  or scol.replace('"','') in sel_cols or \
            misc.isfloat(scol) or scol[:4] in ['cast','trim']: 
            selvalue = f'{ args[col] } as { col }'
        else:
            selvalue = f'NULL as "{ col }" -- couldnt figure out: { scol }'
    else:
        selvalue = f'NULL as "{ col }"'
    cols.append({'ins_name': col, 'ins_value': selvalue })
    log.debug(f"  parsed { col } as value:  { selvalue } ")

# build final SQL:
log.info(f'building final SQL statement, to be saved to { sqlinsert_filepath }')
br = '\n, '
sqlinsert = f"""insert into  { insertinto_tablename }
({ ', '.join([nm['ins_name'] for nm in cols]) })
SELECT
   { br.join([nm['ins_value'] for nm in cols]) }
FROM { selectfrom_tablename } """

sqlinsert_filepath.write_text(sqlinsert)
log.info('File Saved!')
log.debug(('\n' + ('-'*50))*3)
log.debug(sqlinsert)
