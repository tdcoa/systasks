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
thisfilepath = sys.argv[0]
csvfilepath = Path(str(sys.argv[1]).strip()).resolve()     # name of excel / csv file (i.e., "system_cpu.csv")
olddateformat = sys.argv[2].strip()
newdateformat = sys.argv[3].strip()
datecolumnstring = sys.argv[4].strip()

# error testing:
errmsg = f"""Conform_Dates.py ERROR -- expected the following commandline arguments:
     - csv file path == location of the .csv file to be conformed, relative to the "OUT" folder
         received: {csvfilepath}
     - old date format == existing date format, i.e., m/d/yy  or   d/m/yy hh:mm:ss
         received: {olddateformat}
     - new date format == new date format, i.e.,  yyyy/mm/dd  or   yyyy-mm-dd hh:mm:ss
         received: {newdateformat}
     - date column list == comma-separated list of column names to conform, i.e.,  "LogDate,TheDate,UpdateDate" 
         recieved: {datecolumnstring}
"""


if not csvfilepath.exists():
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please    

try:
    datecolumns = list(datecolumnstring.split(','))  # list of column names to conform
except Exception as ex:
    log.error(errmsg)
    raise Exception(errmsg)  # hard error please

log.debug(f'this filepath = {thisfilepath}')
log.debug(f'csv filepath = {csvfilepath}')
log.debug(f'old date format = {olddateformat}')
log.debug(f'new date format = {newdateformat}')
log.debug(f'date columns = {datecolumns}')


def apply_dateformat(inputdate:str) ->str:
    olddtfmt = sjmisc.translate_simple_dateformat(olddateformat)
    newdtfmt = sjmisc.translate_simple_dateformat(newdateformat)
    return datetime.strptime(inputdate, olddtfmt).strftime(newdtfmt)



# def execute(csvfilepath:Path=None):


# make copy of original, just for saftey:
oldcsvfilepath = Path(str(csvfilepath)[:-4] + '---backup.csv')
if not oldcsvfilepath.exists():
    shutil.copy(csvfilepath, oldcsvfilepath)

# load csv into dataframe
df = pd.read_csv(csvfilepath)

# modify all requested date columns
for col in datecolumns:
    df[col] = df[col].apply(apply_dateformat)

# save .csv
df.to_csv(csvfilepath, index=False)


