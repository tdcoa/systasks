from genericpath import exists
from pathlib import Path
from posixpath import supports_unicode_filenames
import sys, glob, shutil 
import pandas as pd 

from sj_misc import sj_Misc as sjmisc

# provided a file match string, will copy the first match to a consistent location
# this overcomes a weakness in COA's IMPORT function, which requires a fixed file name

version = 'v1.0'
#sys.argv = [sys.argv[0], 'destfilepath: temp_gssresusage_upload.csv', 'fuzzyfilepath: ../temp/test/*gssresusage -- Transcend02 -- 2022-03-01*.csv' ]


# use misc logger:
misc = sjmisc(logfilepath='log/{logdate}--fuzzymatch_file_copy.log')
log = misc.log
log.info('\n'+('-'*30)+'\n\tNEW RUN\n'+('-'*30))
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

# parse commandlines
args = misc.parse_namevalue_args(sys.argv, defaults = {'destfilepath':'./temp.tmp'},
                                           required=['fuzzyfilepath'] )

# do glob search to find valid csv file (allowing for glob wildcard characters)
fuzzyfilepath = Path(args['fuzzyfilepath']).resolve()
files = misc.globi(fuzzyfilepath.parent, str(fuzzyfilepath), case_sensitive = False )
srcfilesfound = ''
destexists = ''

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

log.info(f"""Attempting to copy file:
  source:      {srcfilepath}{srcfilesfound}
  destination: {destfilepath}{destexists}""")

try:
    shutil.copy(src=srcfilepath, dst=destfilepath)
    log.info('success!')
except Exception as ex:
    log.error('Failure to copy!')
    log.exception(f'{ex}')