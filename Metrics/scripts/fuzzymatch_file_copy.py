from genericpath import exists
from pathlib import Path
from posixpath import supports_unicode_filenames
import sys, glob, shutil 
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

# provided a file match string, will copy the first match to a consistent location
# this overcomes a weakness in COA's IMPORT function, which requires a fixed file name

version = 'v1.1'
# sys.argv = [sys.argv[0], 'destfilepath: temp_gssresusage_upload.csv', 'fuzzyfilepath: %s/test/*gssresusage -- Transcend02 -- 2022-03-01*.csv' %str(Path(sys.argv[0]).parent) ]

try:
    # use misc logger:
    misc = sjmisc(logfilepath='log/{logdate}--run.log')
    log = misc.log
    log.info('\n'+('-'*30)+'\n\tFUZZY-MATCH FILE COPY\n'+('-'*30))
    log.debug(f'Subscript started: { sys.argv[0] } version { version }')

    # parse commandlines
    args = misc.parse_namevalue_args(sys.argv, defaults = {'destfilepath':'./temp.tmp', 'scriptfilepath':''},
                                            required=['fuzzyfilepath'] )

    # do glob search to find valid csv file (allowing for glob wildcard characters)
    fuzzyfilepath = Path(args['fuzzyfilepath'])
    log.info(f'Searching for files matching pattern: { fuzzyfilepath }')
    files = misc.globi(fuzzyfilepath.parent, str(fuzzyfilepath), case_sensitive = False )
    srcfilesfound = ''
    destexists = ''
except Exception as ex:
    log.exception(f'UNHANDLED EXCEPTION in mapping commandline arguments to variables: \n{ex}')
    raise Exception

try:
    # if no files are found, abort the rest of the processing with an ERROR 
    if len(files) == 0:
        log.exception(f"ABORTING: Could not find any files matching the pattern: { fuzzyfilepath }")
        raise FileNotFoundError(f"ABORTING: Could not find any files matching the pattern: { fuzzyfilepath }")

    elif len(files) >1: # more than one file found, raise WARNING
        log.warning(f"found more than one qualifying file... using the first one encountered.")
        srcfilesfound = f'\n    (found total of {len(files)} qualifying files, using the first recorded)'


    # set all variables
    srcfilepath = Path(files[0]).resolve() # take first one found
    destfilepath = Path(args['destfilepath']).resolve()
    if destfilepath.exists(): 
        log.warning(f'the destination path provided already contains a file - overwriting...')
        destexists = f'\n    (destination file path existed, and will be overwritten)'

except Exception as ex:
    log.exception(f'UNHANDLED EXCEPTION in preparing file source/destination paths: \n{ex}')

log.info(f"""Attempting to copy file:
  source:      {srcfilepath}{srcfilesfound}
  destination: {destfilepath}{destexists}""")

try:
    shutil.copy(src=srcfilepath, dst=destfilepath)
    log.info('success!')
except Exception as ex:
    log.error('Failure to copy!')
    log.exception(f'{ex}')