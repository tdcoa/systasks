from pathlib import Path
from datetime import datetime
import sys, logging
import shutil

version = 'v1.0'

try:
    # add logging
    logformat = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:  %(message)s')
    ts = str(datetime.now().strftime("%Y%m%d-%H%M%S"))
    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    loghandler = logging.FileHandler(f'{ts}-{version} - pregenerate_all_file_placeholders.log', 'w+')
    log.addHandler(loghandler)
except:
    # try to produce an object that won't impede below from at least running...
    log = logging.getLogger(__name__)
    # no handler means no log, but at least no error below...
log.debug('LOGGING STARTED')

# get parent folder, so we can find the right master job file
thisfilepath = sys.argv[0]
jobfilename = sys.argv[1]     # name of calling job file (i.e., "Vantage Health Check.yaml")
extrafilenames = sys.argv[2]  # optional list of files to process (i.e., ["file1.csv","file2.csv"])
jobfile = Path(Path(thisfilepath).parent.parent / jobfilename).resolve()

log.debug(f'thisfilepath = {thisfilepath}')
log.debug(f'jobfilename = {jobfilename}')
log.debug(f'jobfile = {jobfile}')
log.debug(f'extrafilenames = {extrafilenames}')

stubbed_column_count = 21
csv_stub = ','.join(['no_data_%i' %i for i in range(1,stubbed_column_count+1)])  + '\n' + ','.join(['0' for i in range(1,stubbed_column_count+1)])
tsv_stub = '\t'.join(['no_data_%i' %i for i in range(1,stubbed_column_count+1)]) + '\n' + '\t'.join(['0' for i in range(1,stubbed_column_count+1)])



def fix_tsv_content(tsvfilecontent, consecutive_spaces_to_equal_tab:int=2):
    lines = tsvfilecontent.split('\n')
    rows = []
    first_row_column_count = 0

    for line in lines:
        # if it appears to be TSV already, just use the tab delimiter (stripping out extra space)
        if '\t' in line:
            rows.append('\t'.join([str(c).strip() for c in list(line.split('\t'))]))

        # otherwise, proceed to try and guess where tabs go:
        elif line !='':
            cols = []
            colstart = 0
            found_first_nonspace = True
            consecutive_spaces = 0
            end_of_line = False

            for pos in range(0, len(line)):
                end_of_line = pos >= len(line)-1
                char = line[pos:pos+1]
                if char != ' ': found_first_nonspace = True

                if found_first_nonspace or end_of_line:
                    # look if we've traversed 3 spaces consecutively
                    if char == ' ':
                        consecutive_spaces +=1
                    else:
                        consecutive_spaces = 0
                    # if so, capture current column data, and setup for next column
                    if consecutive_spaces >= consecutive_spaces_to_equal_tab or end_of_line:
                        cols.append( line[colstart: pos + end_of_line].strip() )
                        colstart = pos
                        found_first_nonspace = False
                        consecutive_spaces = 0

            # make sure data column count == header column count
            coltxt = '\t'.join(cols)
            column_count = len(coltxt.split('\t'))
            if rows == []:
                first_row_column_count = column_count
            else:
                if column_count < first_row_column_count:
                    cols = coltxt.split('\t')
                    for i in range(0, first_row_column_count - column_count):
                        cols.append('')
                    coltxt = '\t'.join(cols)
                    column_count = len(coltxt.split('\t'))
                elif column_count > first_row_column_count:
                    log.debug(f"you're fucked: your file is all sorts of screwed up. go manually fix it.")

            # append to the final row list, and go to the next line
            rows.append( coltxt )

    # return all rows as one big string
    return '\n'.join(rows)





try:
    files = list(extrafilenames.split(','))
except Exception as ex:
    log.exception(f'error while converting extrafilenames into list object:\n{ex}', stack_info=True)
    files = []

log.debug('\nmanually supplied file: '.join(files))

try:
    # parse out names of all "file: something.csv" in the supplied job.yaml file
    log.debug(f'Open yaml file, to add .csv files from definition source: {jobfilename}')
    if jobfile.exists() and jobfile.suffix == '.yaml':
        with open(jobfile.resolve(), 'r') as fh:
            yamllines = fh.readlines()

        for line in yamllines:
            # make sure all files found are indeed .csv and not {{ templated }}
            if line.strip()[:5] == 'file:' and line.strip()[-4:] == '.csv' and '{{' not in line:
                filename = line.strip()[6:].strip()
                log.debug(f'file auto-found in job: {filename}')
                files.append( filename )
    else:
        log.debug(f'yaml file did not exist, or does not end in .yaml')
except Exception as ex:
    log.debug(f'something went wrong with building file list from yaml:\n{str(ex)}')



log.info('\nFILE LIST BUILD, TIME TO CREATE ANY THAT ARE MISSING OR ZERO-BYTE:')
# for everything found AND everything passed in, create placeholder .csv and .tsv
for file in files:
    print(file)
    try:
        log.debug(f'file: {file}')
        if file.strip()[-4:] == '.csv':
            makefile = False
            csvfile = Path(file)
            tsvfile = Path(file.strip()[:-3] + 'tsv')
            csvfiletemplate =  Path(file.strip()[:-4] + '_template.csv')
            tsvfiletemplate =  Path(file.strip()[:-4] + '_template.tsv')
            if (not csvfile.exists()) or csvfile.stat().st_size == 0:
                log.debug(f'  csv file missing or zero-byte, adding placeholder file...')
                if csvfiletemplate.exists():
                    log.debug(f'  csv _template file found, using instead of generic stub...')
                    shutil.copy(csvfiletemplate, csvfile)
                else:
                    with csvfile.open('w', encoding='utf-8') as fh:
                        fh.write(csv_stub)
                makefile = True
            if (not tsvfile.exists()) or tsvfile.stat().st_size == 0:
                log.debug(f'  tsv file missing or zero-byte, adding placeholder file...')
                if tsvfiletemplate.exists():
                    log.debug(f'  tsv _template file found, using instead of generic stub...')
                    shutil.copy(tsvfiletemplate, tsvfile)
                else:
                    with tsvfile.open('w', encoding='utf-8') as fh:
                        fh.write(tsv_stub)
                makefile = True
            if makefile:
                log.debug('  files CREATED!')
            else:
                log.debug('  files EXIST AS EXPECTED, no action taken')
        else:
            log.warning('  is not a .csv file, ignoring!')

    except Exception as ex:
        log.exception(f'something went wrong with pre-building file: {str(file)}: {str(ex)}', stack_info=True)



# finally, roll thru EVERYTHING one more time and if zero-byte, give it some tsv data
# (same as fix_zerobyte.py )
# this picks up .tsv files that may not appear in the file-list above, but still appear in the folder
log.info(f'\nRolling thru all files in directory, to ensure utf-8 encoding and no zero-byte TSV files remain (in case one existed that wasn''t listed above)')
files = Path('.').glob('*.[c|t]sv')
for file in files:
    try:
        log.debug(f'file examined: {file.name}')


        # get file content:
        if file.stat().st_size == 0:
            filecontent = tsv_stub
            log.debug('  zero-byte file found, using placeholder instead')
        else:
            try:
                with file.open('r', encoding='utf-8') as fh:
                    filecontent = fh.read()
            except UnicodeError as uex:
                try:
                    with file.open('r', encoding='cp1252', errors='ignore') as fh:
                        filecontent = fh.read()
                except Exception as ex:
                    log.exception(f'  encoding was neither utf-8 nor cp1252.  Big bummer face.')
                    raise ex
            except Exception as ex:
                raise ex

            # if we could figure out encoding:
            log.debug(f'  {len(filecontent)} bytes read')

        # ensure that TSV formats are indeed tab-separated values
        log.debug('making sure TSV are, in fact, Tab-Separated Values and not fixed-width')
        filecontent = fix_tsv_content(filecontent)

        # write back file content into uft-8 format:
        log.debug(f'  writing file back as utf-8 format')
        with file.open('w', encoding='utf-8') as fh:
            fh.write(filecontent)

    except Exception as ex:
        log.exception(f'something went wrong with while reformatting file: {str(file)}: {str(ex)}')

log.info('\n\nPROCESS COMPLETE!')
