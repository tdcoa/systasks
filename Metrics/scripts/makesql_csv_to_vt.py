from pathlib import Path
from datetime import datetime
import sys, logging
import glob
from typing import final
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

version = 'v1.0'
# sys.argv = [sys.argv[0], 'debug:False', 'tablename: vt_gssresusage_override', 'csvfilepath: ./test/gssresusage_override -- MENARDS7 -- 2022-02-15*.csv', 'mapfilepath: ./test/gssresusage_map.csv']

try:
    # add logging
    logformat = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:  %(message)s')
    ts = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    filehdlr = logging.FileHandler(f'{ts}-{version} - conform_excel_date_formats.log', 'w+')
    log.addHandler(filehdlr)
    cmdlinehdlr = logging.StreamHandler()
    log.addHandler(cmdlinehdlr)
except:
    # try to produce an object that won't impede below from at least running...
    log = logging.getLogger(__name__)
    # no handler means no log, but at least no error below...
log.debug(f'Subscript started: { sys.argv[0] } version { version }')


# parse args:
misc = sjmisc(log)
args = misc.parse_namevalue_args(sys.argv, defaults = { 'csvfilepath':None, 'mapfilepath':None, 'debug':False } )
scriptfilepath      = Path(args['scriptfilepath']).resolve()
csvfilepath         = Path(args['csvfilepath']).resolve()
if '*' in csvfilepath.name: # contains wildcard
    csvfilepath = Path(glob.glob(str(csvfilepath))[0]).resolve() # take first one found
mapfilepath         = Path(args['mapfilepath']).resolve()
sqlprework_filepath = Path(args['sqlprework_filepath']).resolve() if 'sqlprework_filepath' in args else  scriptfilepath.parent / 'temp' / 'csv2vt_prework.sql'
sqlcreate_filepath   = Path(args['sqlcreate_filepath']).resolve()   if 'sqlcreate_filepath'   in args else  scriptfilepath.parent / 'temp' / 'csv2vt_create.sql'
sqlinsert_filepath   = Path(args['sqlinsert_filepath']).resolve()   if 'sqlinsert_filepath'   in args else  scriptfilepath.parent / 'temp' / 'csv2vt_insert.sql'
finaltablename      = args['tablename'] if 'tablename' in args else 'vt_csv2vt'
preworktablename    = finaltablename + '_prework'
debug               = args['debug'].lower() == 'true'

# error testing:
errmsg = f"""Conform_Dates.py ERROR -- expected the following commandline arguments:
     - csvfilepath == location of the .csv file to be conformed, relative to the "OUT" folder
         received: {csvfilepath}
     - mapfilepath == column map file between source csv and target volatile table.  The final VT looks like the map file.
         received: {mapfilepath}
"""
if not csvfilepath.exists():
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please

if not mapfilepath.exists():
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please

sqlprework_filepath.parent.mkdir(exist_ok=True, parents=True)
sqlcreate_filepath.parent.mkdir(exist_ok=True, parents=True)

log.debug(f'this filepath = {scriptfilepath}')
log.debug(f'csv filepath = {csvfilepath}')
log.debug(f'map filepath = {mapfilepath}')
log.debug(f'sql-prework filepath = {sqlprework_filepath}')
log.debug(f'sql-final filepath = {sqlcreate_filepath}')
log.debug(f'final tablename = {finaltablename}')
log.debug(f'prework tablename = {preworktablename}')
log.debug(f'debug (additional logging) = {debug}')




# Requirements / process flow
# 1 -- Source CSV MUST upload in its entirety
# 2 -- Each CSV MAY be different
# 3 -- Final VT table will match the MAP, including stubbing in columns if missing / leaving out columns from source
# 4 -- Two SQL generated:
#        Create vt_prework Statement (matching csv exactly)
#        Create vt_final as Select * from vt_prework - to match MAP file (and presumably destination table)
# 5 -- other processes will need to
#        call this process to create the two SQL somewhere predictable
#        execute the first.sql file
#        upload the csv into the new vt_prework table
#        execute the second.sql file
#        drop the prework if desired


# 1 -- load the csv into a df
dfcsv = pd.read_csv(csvfilepath)
dfcsv = dfcsv.astype(str)  # convert all to strings, since we're measuring data width, not playing with data itself

dfmap = pd.read_csv(mapfilepath)

# 2 - fill in any NAN from dfmap, so user doesn't have to
dfmap.loc[dfmap['Column_Name_VT'].isnull(), 'Column_Name_VT'] = dfmap['Column_Name_CSV'] # Column_Name_CSV = ColName_CSV if missing
dfmap.loc[dfmap['Column_Default'].isnull(), 'Column_Default'] = '' # Column_Default is set to empty-SQL string if NAN
dfmap.loc[dfmap['Filter1'].isnull(), 'Filter1'] = 'all' # missing filters are assumed as used for ALL
dfmap['Filter1'] = dfmap['Filter1'].str.lower()
dfmap['Column_Type_VT'] = dfmap['Column_Type_VT'].str.upper()
dfmap = dfmap.set_index('Column_Name_CSV')
# if missing, Column_Type is assigned to VARCHAR(max len +10) when the columns are iterated


# build CREATE vt_Prework SQL (driven by CSV for loading)
sqlprework = []
for colcsv in dfcsv.columns:
    # create a map if missing
    if colcsv in dfmap.index:
        mapd = dict(dfmap.loc[colcsv])
        if pd.isnull(mapd['Column_Type_VT']): mapd['Column_Type_VT'] = 'VARCHAR'
    else:
        mapd = {'Column_Name_VT': str(colcsv), 'Column_Type_VT': 'VARCHAR', 'Column_Default':'', 'Filter1': 'all'}

    # if varchar, find max length +10
    if mapd['Column_Type_VT'] == 'VARCHAR':
        colmax = max(dfcsv[colcsv].str.len())+10
        mapd['Column_Type_VT'] = f'VARCHAR({colmax})'

    sqltemp = '"' + str(colcsv+'"').ljust(35," ") + mapd["Column_Type_VT"]
    sqlprework.append(sqltemp)
    if debug: log.debug(f'Prework parsed from CSV: {sqltemp}')

sqlprework = '\n  ,'.join(sqlprework)
sqlprework = f"""create volatile multiset table  {preworktablename} (
   {sqlprework}
) no primary index on commit preserve rows"""

log.debug(sqlprework)
log.debug('\n' + ('-'*50 + '\n')*3 )
sqlprework_filepath.write_text(sqlprework)



# build both CREATE and INSERT (choose one) for vt_final table (driven by map)
sqlfinal = []
sqlinsert = []
for colcsv in list(dfmap.index):
    mapd = dict(dfmap.loc[colcsv])

    #build the correct column definition string:
    quotestr = '"' if colcsv in dfcsv.columns else "'"
    colcsvname = f'{quotestr}{colcsv}{quotestr}'
    if len(mapd['Column_Default'])>0: colcsvname = f"coalesce({colcsvname},{mapd['Column_Default']})"
    colcsvname = colcsvname.ljust(45," ")

    sqltemp = colcsvname + "  as  " + f'"{mapd["Column_Name_VT"]}"'
    sqlfinal.append(sqltemp)
    sqlinsert.append(f""""{mapd['Column_Name_VT']}" """)

    if debug: log.debug(f'Final VT parsed from Map: {sqltemp}')

sqlselectcolumns = '\n  ,'.join(sqlfinal)
sqlcreate = f"""create volatile multiset table  { finaltablename }   as (
SELECT
   { sqlselectcolumns }
FROM { preworktablename }
) with data no primary index on commit preserve rows"""

sqlcreate_filepath.parent.mkdir(exist_ok=True)
sqlcreate_filepath.write_text(sqlcreate)
log.debug(sqlcreate)

log.debug('\n' + ('-'*50 + '\n')*3 )

sqlinsertcolumns = ','.join(sqlinsert)
sqlinsert = f"""insert into  { finaltablename }
({ sqlinsertcolumns })
SELECT
   { sqlselectcolumns }
FROM { preworktablename } """

sqlinsert_filepath.write_text(sqlinsert)
log.debug(sqlinsert)
