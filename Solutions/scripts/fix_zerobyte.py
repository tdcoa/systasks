from pathlib import Path
try:
    newcontent = '\t'.join(['no_data_%i' %i for i in range(1,6)])
    files = Path('.').glob('*')
    for file in files:
        if file.stat().st_size == 0:
            with file.open('w', encoding='utf-8') as f:
                f.write(newcontent)
except:
    print('fix_zerobyte failed for some reason.')
