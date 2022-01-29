import os
from pathlib import Path

for file in os.scandir('.'):
    if file.name.startswith('gssresusagemacro.') and file.name.endswith('.sql'):
        newfilename = file.name.replace('gssresusagemacro.','gssresusage.')
        print("transforming   %s into    %s" %(file.name.ljust(33,' '), newfilename))

        # read in file
        with open(file.path, 'r') as fileh:
            file_lines = fileh.readlines()
            print('   ','original *.macro file contains %i lines' %len(file_lines))

        # remove line 1 - 7, and last line of file
        file_lines = file_lines[7:-1]
        print('   ', 'removing last 1 and first 7 lines, new line #1: %s' %file_lines[0].strip())

        file_lines.insert(0, '/* THIS FILE HAS BEEN DE-MACRO-FIED BY AN AUTOMATED PROCESS. */')
        file_lines.insert(1, '/*   Logic remains intact, but macro wrapper has been removed, */')
        file_lines.insert(2, '/*   parameters have been changed to jinja template parameters, and */')
        file_lines.insert(3, '/*   create volatile table wrapper has been added, to create an abstraction point. */')
        file_lines.insert(4, '')
        file_lines.insert(5, 'CREATE VOLATILE MULTISET TABLE vt_gssresusage_prework as (')
        file_lines.append(") with data  primary index(LogDate, LogTime)  on commit preserve rows")

        # add flexidate logic to the top of the file: -- now in main job
        with Path('../scripts/flexidate.txt').open('r') as fh:
            for i, val in enumerate(fh.readlines()):
                file_lines.insert(i+4, val)

        # do data clean-up per line
        for i, line in enumerate(file_lines):
            file_lines[i] = line.replace('\n','')
            if 'order by' in line: file_lines[i] = line.replace('order by', '--- order by')
            if ';' in line: file_lines[i] = line.replace(';','')


        # perform replace of all four variables
        print('   ', 'replacing macro variables with {{jinja template variables}}')
        filetext = '\n'.join(file_lines)

        findreplace = [[':BEGINDATE' , "{{ startdate | default ('date-45') }}"]
                      ,[':ENDDATE'   , "{{ enddate | default ('date-1')  }}"]
                      ,[':BEGINTIME' , "{{ starttime | default ('0') }}"]
                      ,[':ENDTIME'   , "{{ endtime | default ('240000') }}"]]
        for fr in findreplace:
            filetext = filetext.replace(fr[0], fr[1])

        # save file
        with open(newfilename, 'w') as fileh:
            fileh.write(filetext)
            print('   ','write modified file: %s  (%i lines)' %(newfilename, len(file_lines)))


        print('')
