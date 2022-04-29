from cmath import exp
from pathlib import Path
import shutil, sys
from sj_misc import sj_Misc as sjmisc

version = 'v1.0'
# sys.argv = [sys.argv[0], 'orig_filepath: test/conform_columns_TEST.csv',  'copy_filepath: test/conform_columns_copy.csv' ]


# use misc logger:
misc = sjmisc(logfilepath='log/{logdate}--run.log')
log = misc.log
log.info('\n'+('-'*30)+'\n\tCOPY FILE\n'+('-'*30))
log.debug(f'Subscript started: { sys.argv[0] } version { version }')

try:
    # parse commandlines
    args = misc.parse_namevalue_args(sys.argv, required=['orig_filepath', 'copy_filepath'] )
    src = Path(args['orig_filepath']).resolve()
    dst = Path(args['copy_filepath']).resolve()

    if not src.exists():
        raise FileNotFoundError(f"ABORTING: Could not find SOURCE / ORIGINAL filepath: \n{ src.resolve() }")

    # make sure folderpath for sql exists, and print all variables to log
    log.debug(f'original filepath = { src.resolve() }')
    log.debug(f'copy to  filepath = { dst.resolve() }')

except Exception as ex:
    log.exception(f'UNHANDLED EXCEPTION in mapping commandline arguments to variables: \n{ex}')
    raise Exception

try:
    log.debug(f'Performing copy...')
    shutil.copy(src, dst)
    log.debug(f'Copy complete!')
except Exception as ex:
    log.error(f'Error during copy operation: \n{ ex }')
    raise Exception(ex)
