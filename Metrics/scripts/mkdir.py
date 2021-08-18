import sys, os
if len(sys.argv) >=2:
    if len(sys.argv) >=3: os.chdir(sys.argv[2])
    newfo = sys.argv[1]
    if not os.path.isdir(newfo): os.mkdir(newfo)
