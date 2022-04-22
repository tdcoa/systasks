from pathlib import Path
import sys, glob, shutil 
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

version = 'v1.1'
# sys.argv = [sys.argv[0], 'tablename: vt_gssresusage',  'csvfilepath: test/*gssresusage -- Transcend02 -- 2022-03-01*.csv' ]


# use misc logger:
misc = sjmisc(logfilepath='log/{logdate}--makesql_csv_to_vt.log')
log = misc.log
log.info('\n'+('-'*30)+'\n\tNEW RUN\n'+('-'*30))
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

# parse commandlines
args = misc.parse_namevalue_args(sys.argv, defaults = { 'sqlcreate_filepath': 'temp/makesql_csv_to_vt.sql',
                                                        'debug':False, 'volatile':True},
                                           required=['csvfilepath', 'tablename'] )

# do glob search to find valid csv file (allowing for glob wildcard characters)
csvfilepath = Path(args['csvfilepath']).resolve()
files = glob.glob(str(csvfilepath))

# if no files are found, abort the rest of the processing with an ERROR 
if len(files) == 0:
    log.exception(f"ABORTING: Could not find any files matching the pattern: { csvfilepath }")
    raise FileNotFoundError(f"ABORTING: Could not find any files matching the pattern: { csvfilepath }")

elif len(files) >1: # more than one file found, raise WARNING
    log.warning(f"found more than one qualifying file... using the first one encountered.")


# set all variables
csvfilepath = Path(glob.glob(str(csvfilepath))[0]).resolve() # take first one found
tablename           = args['tablename'] 
volatile            = 'VOLATILE ' if str(args['volatile']).lower() == 'true' else ''
debug               = str(args['debug']).lower() == 'true'
scriptfilepath      = Path(args['scriptfilepath']).resolve()
sqlcreate_filepath  = Path(args['sqlcreate_filepath']).resolve()

# make sure folderpath for sql exists, and print all variables to log
sqlcreate_filepath.parent.mkdir(exist_ok=True, parents=True)
log.debug(f'this filepath = {scriptfilepath}')
log.debug(f'csv filepath = {csvfilepath}')
log.debug(f'tablename = {tablename}')
log.debug(f'volatile table = { args["volatile"] }')
log.debug(f'sql filepath = {sqlcreate_filepath}')
log.debug(f'debug (additional logging) = {debug}')



# 1 -- load the csv into a df
log.debug(f'load dataframe from csv')
dfcsv = pd.read_csv(csvfilepath)
dfcsv = dfcsv.astype(str)  # convert all to strings, since we're measuring data width, not playing with data itself

# iterate over column name/type and build COLUMN  TYPE set
cols = []
for colname, coltype in dict(dfcsv.dtypes).items():
    colmax = max(dfcsv[colname].str.len())+10
    coltype = f'VARCHAR({ colmax })'
    log.debug(f"  assigning column name {colname} a type {coltype} based on csv")
    cols.append(f""""{ str(str(colname) + '"').ljust(32,' ') } { str(coltype) } """)



if debug: log.info(f'build final CREATE {volatile }TABLE sql for : {tablename}')

sqlselectcolumns = '\n  ,'.join(cols)
sqlcreate = f"""create {volatile }multiset table  { tablename }   (
   { sqlselectcolumns }
) no primary index on commit preserve rows"""
log.debug(f'-------- Final SQL:\n {sqlcreate}\n--------\n')

log.debug(f'saving to {sqlcreate_filepath}')
sqlcreate_filepath.write_text(sqlcreate)
log.debug(f'Saved!')
log.info('sql creation complete!')
