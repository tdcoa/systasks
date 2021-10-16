import sys, os, csv
from pathlib import Path

def bteqfix_csv(filepath_csv:Path, filepath_out:Path='') -> list:
    if filepath_out == '': filepath_out = filepath_csv
    newrows = []
    with open(filepath_csv.resolve(), newline='') as fh:
        reader = csv.reader(fh)
        for row in reader:
            newrows.append([x.replace(',','') for x in row])

    with open(filepath_out.resolve(), 'w', newline='') as fh:
        writer = csv.writer(fh, quoting=csv.QUOTE_NONE)
        writer.writerows(newrows)

    return newrows


for i, csvfilepath in enumerate(sys.argv):
    if i >= 1:
        try:
            csvfilepath = Path(sys.argv[i])
            bteqfix_csv(csvfilepath)
        except Exception as e:
            print('SCRIPT ERROR: bteqfix_csv \n%s' %str(e))
