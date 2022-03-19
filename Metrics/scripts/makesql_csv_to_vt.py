from pathlib import Path
from datetime import datetime
import sys, logging
import shutil
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

version = 'v1.0'

try:
    # add logging
    logformat = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:  %(message)s')
    ts = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    loghandler = logging.FileHandler(f'{ts}-{version} - conform_excel_date_formats.log', 'w+')
    log.addHandler(loghandler)
except:
    # try to produce an object that won't impede below from at least running...
    log = logging.getLogger(__name__)
    # no handler means no log, but at least no error below...
log.debug('LOGGING STARTED')


# get parent folder, so we can find the right master job file
thisfilepath = Path(sys.argv[0]).resolve()
csvfilepath = mapfilepath = sqlprework_filepath = sqlfinal_filepath = None 
if len(sys.argv) >= 2:
    csvfilepath = Path(str(sys.argv[1]).strip()).resolve()  # name of excel / csv file to upload (i.e., "gssresusage.csv")
if len(sys.argv) >= 3:
    mapfilepath = Path(str(sys.argv[2]).strip()).resolve()  # map of csv to vt column. At the end of the process, the final VT looks like the map
if len(sys.argv) >= 4:
    sqlprework_filepath = Path(str(sys.argv[3]).strip()).resolve()  # path to save create vt_prework that matches CSV exactly 
else: 
    sqlprework_filepath = thisfilepath.parent / 'temp' / 'csv2vt_prework.sql'
if len(sys.argv) >= 4:
    sqlfinal_filepath = Path(str(sys.argv[3]).strip()).resolve()  # path to save create vt_final as select ** from vt_prework to match the final Map structure
else: 
    sqlfinal_filepath = thisfilepath.parent / 'temp' / 'csv2vt_final.sql'

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

log.debug(f'this filepath = {thisfilepath}')
log.debug(f'csv filepath = {csvfilepath}')
log.debug(f'map filepath = {mapfilepath}')
log.debug(f'sql-prework filepath = {sqlprework_filepath}')
log.debug(f'sql-final filepath = {sqlfinal_filepath}')


# Requirements / process flow
# 1 -- Source CSV MUST upload in its entirety
# 2 -- Each CSV MAY be different
# 3 -- Final VT table will match the MAP, including stubbing in columns if missing / leaving out columns from source
# 4 -- Two SQL generated:  
#        Create vt_prework Statement (matching csv exactly)
#        Create vt_final as Select ** from vt_prework - to match MAP file
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

# fill in any NAN from dfmap, so user doesn't have to
dfmap.loc[dfmap['ColName_VT'].isnull(), 'ColName_VT'] = dfmap['ColName_CSV'] # ColName_VT = ColName_CSV if missing
dfmap.loc[dfmap['Filter1'].isnull(), 'Filter1'] = 'All' # missing filters are assumed as used for ALL 
dfmap['Filter1'] = dfmap['Filter1'].str.lower() 
dfmap['ColType_VT'] = dfmap['ColType_VT'].str.upper() 
dfmap = dfmap.set_index('ColName_CSV')
# if missing, ColType is assigned to VARCHAR(max len +10) when the columns are iterated 


# build CREATE vt_Prework SQL (driven by CSV for loading)
sqlprework = []
for colcsv in dfcsv.columns:
    # create a map if missing
    if colcsv in dfmap.index:
        mapd = dict(dfmap.loc[colcsv])
        if pd.isnull(mapd['ColType_VT']): mapd['ColType_VT'] = 'VARCHAR'
    else:
        mapd = {'ColName_VT': str(colcsv), 'ColType_VT': 'VARCHAR', 'Filter1': 'all'}
    
    # if varchar, find max length +10 
    if mapd['ColType_VT'] == 'VARCHAR':
        colmax = max(dfcsv[colcsv].str.len())+10
        mapd['ColType_VT'] = f'VARCHAR({colmax})'
    
    sqltemp = '"' + str(colcsv+'"').ljust(35," ") + mapd["ColType_VT"]
    sqlprework.append(sqltemp)
    log.debug(f'Prework parsed from CSV: {sqltemp}')
    
sqlprework = '\n  ,'.join(sqlprework)
sqlprework = f"""create volatile multiset table  vt_CSV2VT_Prework (
   {sqlprework}
) no primary index on commit preserve rows"""
 
sqlprework_filepath.parent.mkdir(exist_ok=True)
sqlprework_filepath.write_text(sqlprework)


# build CREATE vt_final as... SQL (driven by map)
sqlfinal = []
for colcsv in list(dfmap.index):
    mapd = dict(dfmap.loc[colcsv])
    # watch the quote types...
    colcsvname = str(f'"{colcsv}"').ljust(35," ") if colcsv in dfcsv.columns else str(f"'{colcsv}'").ljust(35," ")
    sqltemp = colcsvname + "  as  " + f'"{mapd["ColName_VT"]}"'
    sqlfinal.append(sqltemp)

sqlfinal = '\n  ,'.join(sqlfinal)
sqlfinal = f"""create volatile multiset table  vt_CSV2VT   as (
SELECT 
   {sqlfinal}
FROM vt_CSV2VT_Prework
) with data no primary index on commit preserve rows"""
 
sqlfinal_filepath.parent.mkdir(exist_ok=True)
sqlfinal_filepath.write_text(sqlfinal)