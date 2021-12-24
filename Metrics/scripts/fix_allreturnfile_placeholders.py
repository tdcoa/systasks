from pathlib import Path
import sys 

# get parent folder, so we can find the right master job file
thisfilepath = sys.argv[0]  
jobfilename = sys.argv[1]     # name of calling job file (i.e., "Vantage Health Check.yaml")
extrafilenames = sys.argv[2]  # optional list of files to process (i.e., ["file1.csv","file2.csv"])

jobfile = Path(Path(thisfilepath).parent.parent / jobfilename).resolve()


try:
    files = list(extrafilenames)
except: 
    files = []

try:
    # parse out names of all "file: something.csv" in the supplied job.yaml file
    if jobfile.exists() and jobfile.suffix == '.yaml':
        with open(jobfile.resolve(), 'r') as fh:
            yamllines = fh.readlines()

        for line in yamllines:
            # make sure all files found are indeed .csv and not {{ templated }}
            if line.strip()[:5] == 'file:' and line.strip()[-4:] == '.csv' and '{{' not in line:
                files.append( line.strip()[6:].strip() )
except Exception as ex: 
    print(f'something went wrong with building file list from yaml: {str(ex)}')

        
# for everything found AND everything passed in, create placeholder .csv and .tsv
for file in files:
    print(file)
    try:   
        if file.strip()[-4:] == '.csv':
            csvfile = Path(file)
            tsvfile = Path(file.strip()[:-3] + 'tsv')
            if (not csvfile.exists()) or csvfile.stat().st_size == 0:
                with csvfile.open('w', encoding='utf-8') as fh:
                    fh.write(','.join(['no_data_%i' %i for i in range(1,6)]))
            if (not tsvfile.exists()) or tsvfile.stat().st_size == 0:
                with tsvfile.open('w', encoding='utf-8') as fh:
                    fh.write('\t'.join(['no_data_%i' %i for i in range(1,6)]))
    except Exception as ex:
        print(f'something went wrong with pre-building file: {str(file)}: {str(ex)}')

# finally, roll thru EVERYTHING one more time and if zero-byte, give it some tsv data 
# (same as fix_zerobyte.py )
files = Path('.').glob('*')
for file in files:
    try:
        if file.stat().st_size == 0:
            with file.open('w', encoding='utf-8') as f:
                f.write('\t'.join(['no_data_%i' %i for i in range(1,6)]))
    except Exception as ex:
        print(f'something went wrong with filling zero-byte file: {str(file)}: {str(ex)}')